"""
Frienze WebSocket Voice Handler
Real-time voice pipeline: audio in → text → AI → speech out

Protocol (binary/JSON messages over WebSocket):
  Client → Server: binary audio chunk OR JSON control message
  Server → Client: JSON status updates + binary audio response
"""

import json
import logging
import base64
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from services.speech_service import transcribe_audio
from services.emotion_service import detect_emotion, detect_language
from services.llm_service import generate_response
from services.tts_service import synthesize_speech
from services.personality_engine import (
    Personality,
    detect_personality_from_text,
    emotion_to_personality,
    get_personality_display_info,
)

logger = logging.getLogger(__name__)


class VoiceSession:
    """Holds state for a single user's voice session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.personality = Personality.FRIEND
        self.conversation_history: list[dict] = []
        self.language = "en"
        self.ai_name = "Frienze"
        self.audio_buffer = bytearray()
        self.is_recording = False

    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Trim memory to last 40 exchanges
        if len(self.conversation_history) > 40:
            self.conversation_history = self.conversation_history[-40:]


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Main WebSocket entry point."""
    await websocket.accept()
    session = VoiceSession(session_id)
    logger.info(f"WebSocket connected: session={session_id}")

    await _send_json(websocket, {
        "type": "connected",
        "session_id": session_id,
        "personality": session.personality,
        "personality_info": get_personality_display_info(session.personality),
    })

    try:
        while True:
            message = await websocket.receive()

            # Binary: audio chunk
            if "bytes" in message and message["bytes"]:
                session.audio_buffer.extend(message["bytes"])

            # Text: control message
            elif "text" in message:
                await _handle_control(websocket, session, message["text"])

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error [{session_id}]: {e}", exc_info=True)
        await _send_json(websocket, {"type": "error", "message": str(e)})


async def _handle_control(websocket: WebSocket, session: VoiceSession, raw: str):
    """Process JSON control messages from client."""
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        return

    event = msg.get("type")

    if event == "start_recording":
        session.audio_buffer = bytearray()
        session.is_recording = True
        await _send_json(websocket, {"type": "recording_started"})

    elif event == "stop_recording":
        session.is_recording = False
        await _process_voice_turn(websocket, session)

    elif event == "set_personality":
        p = msg.get("personality")
        if p in [e.value for e in Personality]:
            session.personality = Personality(p)
            info = get_personality_display_info(session.personality)
            await _send_json(websocket, {
                "type": "personality_changed",
                "personality": session.personality,
                "personality_info": info,
                "trigger": "manual",
            })

    elif event == "set_language":
        session.language = msg.get("language", "en")

    elif event == "set_ai_name":
        session.ai_name = msg.get("name", "Frienze")

    elif event == "ping":
        await _send_json(websocket, {"type": "pong"})


async def _process_voice_turn(websocket: WebSocket, session: VoiceSession):
    """Full pipeline: audio → text → personality → LLM → TTS → audio out."""
    audio_bytes = bytes(session.audio_buffer)
    session.audio_buffer = bytearray()

    if len(audio_bytes) < 1000:
        await _send_json(websocket, {"type": "too_short"})
        return

    # ── Step 1: Speech Recognition ───────────────────────────────────────────
    await _send_json(websocket, {"type": "processing", "step": "transcribing"})
    try:
        stt_result = await transcribe_audio(audio_bytes, language=session.language or None)
    except Exception as e:
        await _send_json(websocket, {"type": "error", "message": f"Speech recognition failed: {e}"})
        return

    user_text = stt_result["text"]
    detected_lang = stt_result.get("language", "en")
    session.language = detected_lang

    if not user_text.strip():
        await _send_json(websocket, {"type": "no_speech"})
        return

    await _send_json(websocket, {
        "type": "transcription",
        "text": user_text,
        "language": detected_lang,
    })

    # ── Step 2: Personality Detection ────────────────────────────────────────
    trigger_personality = detect_personality_from_text(user_text)
    personality_trigger = "trigger_word"

    if trigger_personality:
        new_personality = trigger_personality
    else:
        # Emotion-based selection
        emotion, confidence = await detect_emotion(user_text)
        new_personality = emotion_to_personality(emotion)
        personality_trigger = f"emotion:{emotion}"

        await _send_json(websocket, {
            "type": "emotion_detected",
            "emotion": emotion,
            "confidence": round(confidence, 2),
        })

    # Notify if personality switched
    if new_personality != session.personality:
        session.personality = new_personality
        info = get_personality_display_info(session.personality)
        await _send_json(websocket, {
            "type": "personality_changed",
            "personality": session.personality,
            "personality_info": info,
            "trigger": personality_trigger,
        })

    # ── Step 3: LLM Response ─────────────────────────────────────────────────
    await _send_json(websocket, {"type": "processing", "step": "thinking"})
    session.add_message("user", user_text)

    try:
        ai_text = await generate_response(
            user_message=user_text,
            personality=session.personality,
            conversation_history=session.conversation_history[:-1],  # exclude current
            ai_name=session.ai_name,
            language=detected_lang,
        )
    except Exception as e:
        await _send_json(websocket, {"type": "error", "message": f"AI response failed: {e}"})
        return

    session.add_message("assistant", ai_text)
    await _send_json(websocket, {"type": "ai_text", "text": ai_text})

    # ── Step 4: Text-to-Speech ───────────────────────────────────────────────
    await _send_json(websocket, {"type": "processing", "step": "speaking"})
    try:
        audio_out = await synthesize_speech(ai_text, session.personality)
    except Exception as e:
        await _send_json(websocket, {"type": "error", "message": f"TTS failed: {e}"})
        return

    # Send audio as base64 in JSON (simpler than binary framing)
    audio_b64 = base64.b64encode(audio_out).decode()
    await _send_json(websocket, {
        "type": "audio_response",
        "audio_base64": audio_b64,
        "format": "mp3",
        "personality": session.personality,
    })


async def _send_json(ws: WebSocket, data: dict):
    try:
        await ws.send_text(json.dumps(data))
    except Exception:
        pass
