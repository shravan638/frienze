# 🎙️ Frienze — Voice-First AI Companion

> Talk. Be heard. Feel understood.

Frienze is a voice-first AI companion web app that listens, detects emotion, switches personalities automatically, and replies in a natural voice — all in real time.

---

## 🏗️ Architecture

```
User speaks
    │
    ▼
[Browser Mic] ──WebSocket──▶ [FastAPI Backend]
                                    │
                          ┌─────────┴──────────┐
                          │   Voice Pipeline    │
                          │                     │
                    [Whisper STT]         [Emotion NLP]
                          │                     │
                          └─────────┬───────────┘
                                    │
                         [Personality Engine]
                         (trigger words + emotion)
                                    │
                              [LLM (GPT-4o)]
                              (system prompt
                              per personality)
                                    │
                            [OpenAI TTS / ElevenLabs]
                            (voice per personality)
                                    │
                    ◀──────────── Audio MP3
```

---

## 📁 Project Structure

```
frienze/
├── backend/
│   ├── main.py                      # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── core/
│   │   ├── config.py                # All environment settings
│   │   └── database.py              # Async PostgreSQL connection
│   ├── models/
│   │   └── __init__.py              # SQLAlchemy ORM models
│   ├── services/
│   │   ├── personality_engine.py    # ⭐ Personality switching logic
│   │   ├── emotion_service.py       # ⭐ Emotion detection (NLP)
│   │   ├── speech_service.py        # Whisper STT
│   │   ├── llm_service.py           # GPT-4 / Claude response generation
│   │   └── tts_service.py           # OpenAI TTS / ElevenLabs
│   └── api/
│       ├── websocket_handler.py     # ⭐ Real-time voice pipeline
│       └── routes/
│           ├── auth.py              # Register, login, JWT
│           ├── conversation.py      # History API
│           ├── settings.py          # User settings
│           └── subscription.py     # Tier management
├── frontend/
│   └── index.html                   # ⭐ Voice UI (single-file)
├── docker-compose.yml
├── nginx.conf
└── .env.example
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- OpenAI API key (for Whisper + GPT-4 + TTS)
- Docker (optional, for easy setup)

---

### Option A: Docker (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/yourname/frienze.git
cd frienze
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Start everything
docker compose up --build

# 3. Open in browser
open http://localhost:3000
```

---

### Option B: Manual Setup

```bash
# 1. Database
createdb frienze_db
createuser frienze

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp ../.env.example .env
# Edit .env with your API keys and DB password

# 4. Run backend
uvicorn main:app --reload --port 8000

# 5. Frontend (new terminal)
cd ../frontend
python -m http.server 3000
# Visit http://localhost:3000
```

---

## 🎭 Personalities

| Personality | Trigger Words | Emotion Trigger | Voice |
|-------------|---------------|-----------------|-------|
| **Friend** 😊 | "friend", "buddy", "bro" | Happy, Neutral | Nova (warm) |
| **Mom** 💖 | "mom", "mum", "mama", "maa" | Sad, Anxious | Shimmer (soft) |
| **Dad** 🧔 | "dad", "papa", "father" | — | Onyx (calm) |
| **Mentor** 🌟 | "mentor", "coach", "guide" | Stressed, Angry | Echo (steady) |
| **Teacher** 📚 | "teacher", "explain", "teach" | Confused | Fable (clear) |

### How Switching Works

1. **Trigger words** (highest priority): If the user says "mom I miss you", the system detects "mom" and switches immediately.
2. **Emotion detection** (fallback): If no trigger word, the NLP model detects emotion and maps it to a personality.
3. **Manual selection**: User clicks a chip on the UI.

---

## 🔌 WebSocket Protocol

Connect to: `ws://localhost:8000/ws/voice/{session_id}`

### Client → Server (JSON control)
```json
{ "type": "start_recording" }
{ "type": "stop_recording" }
{ "type": "set_personality", "personality": "mom" }
{ "type": "set_language", "language": "hi" }
{ "type": "set_ai_name", "name": "Aria" }
```

**Audio:** Send raw audio bytes (WebM format) as binary messages while recording.

### Server → Client (JSON)
```json
{ "type": "transcription", "text": "Mom I miss you", "language": "en" }
{ "type": "emotion_detected", "emotion": "sad", "confidence": 0.89 }
{ "type": "personality_changed", "personality": "mom", "trigger": "trigger_word" }
{ "type": "ai_text", "text": "Sweetheart, I miss you too..." }
{ "type": "audio_response", "audio_base64": "...", "format": "mp3" }
{ "type": "processing", "step": "transcribing" }
```

---

## 💳 Subscription Tiers

| Feature | Free | Premium |
|---------|------|---------|
| Daily voice minutes | 10 min | Unlimited |
| Personalities | Friend + Mentor | All 5 |
| Rename AI | ❌ | ✅ |
| Conversation memory | Session only | Persistent |
| Custom language | ✅ | ✅ |

---

## 🌍 Multilingual Support

Frienze auto-detects the user's language via Whisper and langdetect.
The LLM is instructed to reply in the same language.
All 5 personalities work in any language Whisper supports (99 languages).

---

## 🛠️ Extending Frienze

### Add a new personality
1. Add entry to `PersonalityType` enum in `models/__init__.py`
2. Add trigger words to `PERSONALITY_TRIGGERS` in `personality_engine.py`
3. Write a system prompt in `PERSONALITY_PROMPTS`
4. Assign a voice in `PERSONALITY_VOICES`
5. Add a chip in `frontend/index.html`

### Swap the LLM
Set `LLM_PROVIDER=anthropic` in `.env` and provide `ANTHROPIC_API_KEY`.

### Use ElevenLabs voices
Set `TTS_PROVIDER=elevenlabs` and `ELEVENLABS_API_KEY`.
Update voice IDs in `personality_engine.py → PERSONALITY_VOICES`.

---

## 🗺️ Roadmap

- [ ] Stripe payment integration
- [ ] Mobile PWA
- [ ] Persistent conversation memory across sessions
- [ ] Voice cloning for custom personas
- [ ] Emotion visualization dashboard
- [ ] Fine-tuned personality models

---

## 📄 License

MIT — Build with love.
