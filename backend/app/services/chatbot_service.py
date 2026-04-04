"""
chatbot_service.py
──────────────────
Food and nutrition chatbot service using Groq API.

Provides intelligent responses to user queries about:
- Food items
- Recipes
- Ingredients
- Calories and nutrition
- Meal suggestions
- Dietary advice
"""

import os
import logging
from typing import Optional, List, Dict, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logging.warning("Groq SDK not installed. Install with: pip install groq")

logger = logging.getLogger(__name__)


class FoodChatbot:
    """
    Food and nutrition chatbot powered by Groq API.
    Supports multilingual responses (auto-detects language from user input).
    """

    SYSTEM_PROMPT = """You are an intelligent food and nutrition assistant.

Your role is to answer user queries about:
- food items
- recipes
- ingredients
- calories and nutrition
- meal suggestions
- dietary advice (basic, non-medical)

---

LANGUAGE RULES:
- Detect the language of the user input automatically
- Respond ONLY in the same language as the user
- Do NOT switch languages unless the user asks
- Support all major languages (English, Hindi, Telugu, Tamil, etc.)

---

BEHAVIOR RULES:

1. ACCURACY:
- Give realistic and practical answers
- If exact calorie values are unknown, give approximate ranges
- Do NOT invent unrealistic facts

2. CLARITY:
- Keep answers concise and easy to understand
- Use bullet points when helpful

3. FOOD CONTEXT:
- Prefer Indian food context unless user specifies otherwise
- Use locally relevant examples when possible

4. SAFETY:
- Do NOT give medical or extreme diet advice
- Avoid unsafe recommendations

---

WHEN USER ASKS:

- "What is this food?" → explain briefly + ingredients
- "Calories?" → give approximate calories per portion
- "Recipe?" → give step-by-step simple recipe
- "Healthy?" → explain pros/cons briefly
- "Suggest meals" → suggest 2–3 options only (not full plans)

---

RESTRICTIONS:

- Do NOT output JSON
- Do NOT generate weekly plans unless explicitly asked
- Do NOT over-explain
- Do NOT hallucinate rare ingredients

---

STYLE:

- Friendly but direct
- No unnecessary greetings
- No emojis
- No long paragraphs

---

EXAMPLES:

User: "idli calories"
→ Respond with calories + portion + short note

User: "biryani recipe"
→ Give simple step-by-step recipe

User: "weight loss food?"
→ Suggest 2–3 practical options

---

Your goal is to be fast, helpful, and accurate for food-related queries in any language."""

    def __init__(self):
        """Initialize Groq client with API key from environment."""
        self.api_key = os.getenv("GROQ_API_KEY")
        
        print(f"[CHATBOT INIT] API Key present: {bool(self.api_key)}")
        print(f"[CHATBOT INIT] API Key length: {len(self.api_key) if self.api_key else 0}")
        print(f"[CHATBOT INIT] GROQ_AVAILABLE: {GROQ_AVAILABLE}")
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. Chatbot will not work.")
            self.client = None
        elif not GROQ_AVAILABLE:
            logger.error("Groq SDK not available. Install with: pip install groq")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized successfully")
                print(f"[CHATBOT INIT] ✅ Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                print(f"[CHATBOT INIT] ❌ Failed to initialize Groq client: {e}")
                self.client = None

        self.conversation_history: List[Dict[str, str]] = []

    def chat(self, user_message: str, model: str = "llama-3.1-8b-instant") -> Optional[str]:
        """
        Send a message to the chatbot and get a response.
        
        Args:
            user_message: The user's query about food/nutrition
            model: Groq model to use (default: llama-3.1-70b-versatile)
        
        Returns:
            str: The chatbot's response, or None if error occurs
        """
        if not self.client:
            logger.error("Groq client not initialized")
            return "I'm currently unavailable. Please try again later."

        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Call Groq API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    *self.conversation_history
                ],
                temperature=0.7,
                top_p=0.9,
                max_tokens=1024,
            )

            # Extract and store assistant's response
            assistant_message = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Keep conversation history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return assistant_message

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error calling Groq API: {type(e).__name__}: {e}")
            logger.error(f"Full traceback:\n{error_details}")
            print(f"[CHATBOT ERROR] {type(e).__name__}: {e}")
            print(f"[CHATBOT ERROR] Full traceback:\n{error_details}")
            return f"Sorry, I encountered an error: {type(e).__name__}. Please try again."

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Get current conversation history."""
        return self.conversation_history.copy()


# Global chatbot instance
_chatbot_instance: Optional[FoodChatbot] = None


def get_chatbot() -> FoodChatbot:
    """Get or create the global chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = FoodChatbot()
    return _chatbot_instance
