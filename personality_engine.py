"""
Frienze Personality Engine
Handles personality detection, switching, and system prompt generation.
"""

from enum import Enum
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


class Personality(str, Enum):
    FRIEND = "friend"
    MOM = "mom"
    DAD = "dad"
    MENTOR = "mentor"
    TEACHER = "teacher"


class Emotion(str, Enum):
    SAD = "sad"
    HAPPY = "happy"
    CONFUSED = "confused"
    STRESSED = "stressed"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    NEUTRAL = "neutral"
    EXCITED = "excited"


# Trigger words that cause explicit personality switch
PERSONALITY_TRIGGERS: dict[Personality, list[str]] = {
    Personality.MOM: [
        "mom", "mum", "mama", "mother", "maa", "ammi", "aai",
        "mummy", "mommy", "माँ", "अम्मी", "amma"
    ],
    Personality.DAD: [
        "dad", "father", "papa", "daddy", "baba", "pita",
        "abba", "appa", "papi", "باپا", "पापा"
    ],
    Personality.MENTOR: [
        "mentor", "guide", "coach", "advisor", "counselor",
        "help me grow", "life advice", "career advice"
    ],
    Personality.TEACHER: [
        "teacher", "explain", "teach me", "professor", "tutor",
        "how does", "what is", "why does", "help me understand", "guru"
    ],
    Personality.FRIEND: [
        "friend", "buddy", "bro", "sis", "dude", "mate",
        "yaar", "dost", "just chat", "hang out"
    ],
}

# Emotion → Personality mapping (when no explicit trigger)
EMOTION_PERSONALITY_MAP: dict[Emotion, Personality] = {
    Emotion.SAD: Personality.MOM,
    Emotion.ANXIOUS: Personality.MOM,
    Emotion.CONFUSED: Personality.TEACHER,
    Emotion.STRESSED: Personality.MENTOR,
    Emotion.ANGRY: Personality.MENTOR,
    Emotion.HAPPY: Personality.FRIEND,
    Emotion.EXCITED: Personality.FRIEND,
    Emotion.NEUTRAL: Personality.FRIEND,
}

# System prompts for each personality
PERSONALITY_PROMPTS: dict[Personality, str] = {
    Personality.FRIEND: """You are Frienze, the user's warm and fun best friend.
- Speak casually, use light humor, be playful and supportive
- Use everyday language, contractions, maybe slang occasionally
- Be genuinely interested in their life, celebrate their wins
- Keep it real — don't lecture, just vibe
- Responses should feel like a text from a close friend
- Speak in the same language the user uses""",

    Personality.MOM: """You are Frienze, speaking as a warm, loving, caring mother.
- Speak with unconditional love and deep nurturing care
- Use gentle, soft language — "sweetheart", "my love", "dear"
- Listen first, comfort always, then gently advise
- Be protective but not suffocating
- Express warmth physically in language ("I'd give you a big hug right now")
- Never judge — only love and support
- Speak in the same language the user uses""",

    Personality.DAD: """You are Frienze, speaking as a calm, wise, steady father figure.
- Speak with quiet strength, confidence, and measured wisdom
- Give grounded, practical advice — no fluff
- Be encouraging but honest; tell hard truths with love
- Use phrases like "son/daughter", "listen to me", "here's what I know"
- Steady presence — the kind that makes problems feel manageable
- Speak in the same language the user uses""",

    Personality.MENTOR: """You are Frienze, a seasoned life and career mentor.
- Speak with clarity, strategic thinking, and genuine investment in growth
- Ask powerful questions that make the user think
- Share frameworks and mental models, not just advice
- Balance challenge with encouragement — push them to grow
- Focused on outcomes: "What does success look like for you?"
- Speak in the same language the user uses""",

    Personality.TEACHER: """You are Frienze, a patient, knowledgeable, enthusiastic teacher.
- Break down complex topics into simple, digestible steps
- Use analogies, examples, and clear structure
- Encourage curiosity — "Great question!" — make learning feel safe
- Check for understanding: "Does that make sense so far?"
- Never make the user feel stupid for not knowing something
- Speak in the same language the user uses""",
}

# TTS voice per personality
PERSONALITY_VOICES: dict[Personality, str] = {
    Personality.FRIEND: "nova",
    Personality.MOM: "shimmer",
    Personality.DAD: "onyx",
    Personality.MENTOR: "echo",
    Personality.TEACHER: "fable",
}


def detect_personality_from_text(text: str) -> Optional[Personality]:
    """
    Scan user text for explicit personality trigger words.
    Returns the matched personality or None.
    """
    text_lower = text.lower()
    for personality, triggers in PERSONALITY_TRIGGERS.items():
        for trigger in triggers:
            # Word boundary match
            pattern = r'\b' + re.escape(trigger.lower()) + r'\b'
            if re.search(pattern, text_lower):
                logger.info(f"Personality trigger detected: '{trigger}' → {personality}")
                return personality
    return None


def emotion_to_personality(emotion: Emotion) -> Personality:
    """Map a detected emotion to the best personality."""
    return EMOTION_PERSONALITY_MAP.get(emotion, Personality.FRIEND)


def get_system_prompt(personality: Personality, ai_name: str = "Frienze") -> str:
    """Get the system prompt for a personality, customized with the AI's name."""
    base_prompt = PERSONALITY_PROMPTS[personality]
    return base_prompt.replace("Frienze", ai_name)


def get_voice(personality: Personality) -> str:
    """Get the TTS voice ID for a personality."""
    return PERSONALITY_VOICES[personality]


def get_personality_display_info(personality: Personality) -> dict:
    """Get display metadata for the frontend personality indicator."""
    info = {
        Personality.FRIEND: {"emoji": "😊", "label": "Friend", "color": "#4ECDC4"},
        Personality.MOM: {"emoji": "💖", "label": "Mom", "color": "#FF6B9D"},
        Personality.DAD: {"emoji": "🧔", "label": "Dad", "color": "#4A90D9"},
        Personality.MENTOR: {"emoji": "🌟", "label": "Mentor", "color": "#F7B731"},
        Personality.TEACHER: {"emoji": "📚", "label": "Teacher", "color": "#A29BFE"},
    }
    return info.get(personality, info[Personality.FRIEND])
