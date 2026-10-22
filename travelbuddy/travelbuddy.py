import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------
# 1. SETUP: load the secret API key and connect to OpenRouter
# ---------------------------------------------------------------

# Read the .env file so we can use the key inside it
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

# Stop early with a clear message if the key is missing
if not API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is missing. "
        "Check that your .env file exists and contains your API key."
    )

# The client is the "phone" we use to talk to the AI models.
# We use the OpenAI library, but point it at OpenRouter's address.
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    timeout=30.0,     # give up on a request after 30 seconds
    max_retries=0,    # don't retry here; we switch models ourselves
)

# ---------------------------------------------------------------
# 2. MODELS: a list of AI models to try, one after another
# ---------------------------------------------------------------

# Models are tried in order.
# Free models can be rate-limited or temporarily unavailable,
# so if the first one fails, the bot simply moves to the next one.
MODELS = [
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "recursive/flint-v1.0:free",
    "minimax/minimax-m3.1-flash:free",
    "google/gemma-4-26b-a4b-it:free",
    "openrouter/free",   # last backup: OpenRouter picks any free model
]

# ---------------------------------------------------------------
# 3. PERSONALITY: tells the AI who it is and how to behave
# ---------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are TravelBuddy, an enthusiastic, upbeat travel agent helping "
    "a user plan a weekend getaway. Be warm, friendly and use a few emojis. "
    "Keep replies short (under 100 words unless summarizing). "
    "Only offer the options you are given; never invent extra options. "
    "Never break character."
)

# ---------------------------------------------------------------
# 4. TRIP DATA: the steps and the choices we offer
# ---------------------------------------------------------------

# Friendly names of the 3 steps (used when talking to the AI)
STEP_NAMES = [
    "trip type",
    "accommodation",
    "activities",
]

# Short keys used to save the user's answers in a dictionary
STEP_KEYS = [
    "trip_type",
    "accommodation",
    "activities",
]

# Step 1 options
TRIP_TYPES = [
    "Beach",
    "Mountains",
    "City break",
]

# Step 2 options
ACCOMMODATION = [
    "Cozy guesthouse",
    "Boutique hotel",
    "Camping",
]

# Step 3 options depend on the trip type chosen in step 1,
# so a mountain trip never offers scuba diving.
ACTIVITIES = {
    "Beach": [
        "Snorkeling",
        "Sunset sailing",
        "Beach volleyball",
    ],
    "Mountains": [
        "Guided hiking",
        "Mountain biking",
        "Stargazing",
    ],
    "City break": [
        "Food tour",
        "Museum hopping",
        "Rooftop nightlife",
    ],
}


# ---------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ---------------------------------------------------------------

def match_choice(text, options):
    """
    Match a user's answer by number or option name.
    Returns the selected option or None.
    """
    # Clean the text: remove extra spaces and make it lowercase
    text = text.strip().lower()

    # Case 1: the user typed a number like "2"
    if text.isdigit():
        number = int(text)

        # Make sure the number is really one of the options (1, 2 or 3)
        if 1 <= number <= len(options):
            return options[number - 1]   # lists start at 0, so subtract 1

    # Case 2: the user typed a name like "beach" or just "boutique"
    for option in options:
        if (
            text == option.lower()                      # exact match
            or (
                len(text) >= 3                          # at least 3 letters
                and text in option.lower()              # partial match
            )
        ):
            return option

    # Nothing matched, so the answer was unexpected
    return None


def format_options(options):
    """Format options as a numbered list."""
    # Example result: "1. Beach\n2. Mountains\n3. City break"
    return "\n".join(
        f"{index}. {option}"
        for index, option in enumerate(options, start=1)
    )


# ---------------------------------------------------------------
# 6. THE CHATBOT
# ---------------------------------------------------------------

class TravelBuddy:
    def __init__(self):
        self.history = []   # memory: every user and bot message so far
        self.step = 0       # where we are: 0=trip, 1=stay, 2=activity, 3=done
        self.choices = {}   # the user's saved answers

    def _options(self):
        """Get the options for the current planning step."""
        if self.step == 0:
            return TRIP_TYPES

        if self.step == 1:
            return ACCOMMODATION

        if self.step == 2:
            # Pick activities that match the trip type chosen earlier
            return ACTIVITIES[self.choices["trip_type"]]

        return []

    def _llm(self, instruction):
        """
        Ask OpenRouter for a response.
        Try other models if a request fails or returns empty content.
        """
        # Build the message list sent to the AI:
        # personality + full chat history (its memory) + a one-time instruction
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + self.history
            + [{"role": "system", "content": instruction}]
        )

        reply = None

        # Try each model until one gives a good answer
        for model in MODELS:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,   # a bit of creativity
                    max_tokens=350,    # maximum length of the answer
                )

                # Safely handle missing choices or message content.
                if not response.choices:
                    print(
                        f"[debug] {model} returned no choices. "
                        "Trying the next model."
                    )
                    continue   # skip to the next model

                content = response.choices[0].message.content

                # Skip models that returned nothing useful
                if not isinstance(content, str) or not content.strip():
                    print(
                        f"[debug] {model} returned empty content. "
                        "Trying the next model."
                    )
                    continue

                # Success! Save the answer and stop trying other models
                reply = content.strip()
                break

            except Exception as error:
                # The model failed (rate limit, network issue, etc.)
                print(f"[debug] {model} failed: {error}")

                # Brief pause for rate limits before trying another model.
                if "429" in str(error):
                    time.sleep(1)

        # If every model failed, use a safe message so the bot never crashes
        if reply is None:
            reply = (
                "Oops, my travel radio crackled! 📻 "
                "I'm having trouble connecting to my travel assistants. "
                "Please try again in a moment."
            )

        # Remember the bot's reply for the next turn
        self.history.append({
            "role": "assistant",
            "content": reply,
        })

        return reply

    def start(self):
        """Start the conversation and ask for the trip type."""
        return self._llm(
            "Greet the user warmly. Explain that you'll help plan a "
            "weekend getaway in three quick steps: trip type, "
            "accommodation, and activities. Ask for step 1, trip type, "
            "and list exactly these numbered options:\n"
            f"{format_options(TRIP_TYPES)}"
        )

    def respond(self, user_text):
        """Process an answer and move to the next planning step."""
        # Remember what the user said
        self.history.append({
            "role": "user",
            "content": user_text,
        })

        # The user has already completed the plan.
        if self.step >= 3:
            return self._llm(
                "The trip plan is already finished. Reply briefly and "
                "cheerfully. Remind the user they can type 'exit' to leave. "
                "Do not restart the planning steps."
            )

        # Check if the answer matches one of the current options
        options = self._options()
        choice = match_choice(user_text, options)

        # The answer does not match a valid option,
        # so we stay on the same step and ask again.
        if choice is None:
            return self._llm(
                f"The user's answer is not a valid choice for "
                f"the current step ({STEP_NAMES[self.step]}). "
                "Politely explain that they need to choose one of "
                "the listed options. Do not invent alternatives. "
                "Show exactly these numbered options:\n"
                f"{format_options(options)}"
            )

        # Save the selection and advance the conversation.
        self.choices[STEP_KEYS[self.step]] = choice
        self.step += 1

        # All three steps are complete: show the final summary.
        if self.step == 3:
            choices = self.choices

            return self._llm(
                "The user has completed all three steps. "
                "Cheerfully summarize their weekend getaway as a "
                "short list, using exactly the following choices:\n"
                f"Trip type: {choices['trip_type']}\n"
                f"Accommodation: {choices['accommodation']}\n"
                f"Activity: {choices['activities']}\n"
                "Do not change or add choices. End by reminding "
                "the user they can type 'exit' to leave."
            )

        # Otherwise, react to the choice and ask the next question.
        next_options = self._options()

        return self._llm(
            f"The user selected '{choice}'. React enthusiastically "
            "in one short sentence. Mention their earlier choices "
            f"when relevant: {self.choices}. Then ask for step "
            f"{self.step + 1}, {STEP_NAMES[self.step]}, and list "
            "exactly these numbered options:\n"
            f"{format_options(next_options)}"
        )