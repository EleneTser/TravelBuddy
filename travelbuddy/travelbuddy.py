import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Primary model first, then a free fallback (check openrouter.ai/models for current free ones)
MODELS = [
    "meta-llama/llama-3-8b-instruct",
    "meta-llama/llama-3.2-3b-instruct:free",
]

SYSTEM_PROMPT = (
    "You are TravelBuddy, an enthusiastic, upbeat travel agent helping a user plan "
    "a weekend getaway. Be warm, friendly and use a few emojis. Keep replies short "
    "(under 100 words unless summarizing). Only offer the options you are given; "
    "never invent extra options. Never break character."
)

STEP_NAMES = ["trip type", "accommodation", "activities"]
STEP_KEYS = ["trip_type", "accommodation", "activities"]

TRIP_TYPES = ["Beach", "Mountains", "City break"]
ACCOMMODATION = ["Cozy guesthouse", "Boutique hotel", "Camping"]
ACTIVITIES = {
    "Beach": ["Snorkeling", "Sunset sailing", "Beach volleyball"],
    "Mountains": ["Guided hiking", "Mountain biking", "Stargazing"],
    "City break": ["Food tour", "Museum hopping", "Rooftop nightlife"],
}


def match_choice(text, options):
    """Match by number ('2') or by name/partial name ('boutique'). Returns option or None."""
    text = text.strip().lower()
    if text.isdigit() and 1 <= int(text) <= len(options):
        return options[int(text) - 1]
    for opt in options:
        if text == opt.lower() or (len(text) >= 3 and text in opt.lower()):
            return opt
    return None


def format_options(options):
    return "\n".join(f"{i}. {o}" for i, o in enumerate(options, 1))


class TravelBuddy:
    def __init__(self):
        self.history = []   # conversation memory (user + assistant turns)
        self.step = 0       # 0=trip type, 1=accommodation, 2=activities, 3=done
        self.choices = {}

    # ---------- helpers ----------
    def _options(self):
        if self.step == 0:
            return TRIP_TYPES
        if self.step == 1:
            return ACCOMMODATION
        return ACTIVITIES[self.choices["trip_type"]]

    def _llm(self, instruction):
        """Send full history + a one-off instruction; store and return the reply."""
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + self.history
            + [{"role": "system", "content": instruction}]
        )
        reply = None
        for model in MODELS:
            try:
                resp = client.chat.completions.create(
                    model=model, messages=messages, temperature=0.7, max_tokens=350
                )
                reply = resp.choices[0].message.content.strip()
                break
            except Exception as e:
                print(f"[debug] {model} failed: {e}")
        if not reply:  # never crash: static fallback
            reply = "Oops, my travel radio crackled! 📻 Could you say that again?"
        self.history.append({"role": "assistant", "content": reply})
        return reply

    # ---------- public API ----------
    def start(self):
        return self._llm(
            "Greet the user warmly, say you'll help plan a weekend getaway in 3 quick "
            "steps (trip type, accommodation, activities). Then ask for step 1, the trip "
            f"type, and list exactly these numbered options:\n{format_options(self._options())}"
        )

    def respond(self, user_text):
        self.history.append({"role": "user", "content": user_text})

        if self.step >= 3:
            return self._llm(
                "The trip plan is already finished. Reply briefly and cheerfully, and "
                "remind the user they can type 'exit' to leave."
            )

        options = self._options()
        choice = match_choice(user_text, options)

        if choice is None:  # unexpected answer -> steer back
            return self._llm(
                f"The user's last message was NOT one of the valid choices for the "
                f"current step ({STEP_NAMES[self.step]}). Playfully acknowledge what they "
                f"said, explain kindly you can't arrange that, and guide them back by "
                f"asking again with exactly these numbered options:\n{format_options(options)}"
            )

        self.choices[STEP_KEYS[self.step]] = choice
        self.step += 1

        if self.step == 3:
            c = self.choices
            return self._llm(
                "The user finished all steps. Cheerfully summarize the final weekend plan "
                f"as a short list: Trip type: {c['trip_type']}; Accommodation: "
                f"{c['accommodation']}; Activity: {c['activities']}. End by saying they "
                "can type 'exit' to leave."
            )

        return self._llm(
            f"The user chose '{choice}'. React enthusiastically in one sentence, "
            f"mentioning their earlier choices if relevant ({self.choices}). Then ask for "
            f"step {self.step + 1}, {STEP_NAMES[self.step]}, listing exactly these "
            f"numbered options:\n{format_options(self._options())}"
        )