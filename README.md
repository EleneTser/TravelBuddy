# 🧳 TravelBuddy

A console chatbot that acts as an enthusiastic travel agent and helps you plan a weekend getaway. It guides you step by step through **trip type → accommodation → activities**, offering 3 options at each step, then summarizes your final plan.

## Features

- Upbeat, friendly travel-agent personality
- Three guided steps with 3 options each
- Activities that match the chosen trip type (mountains never suggest scuba diving)
- Conversation history is preserved, so the bot remembers earlier choices
- Handles unexpected answers (e.g. "I want to stay on the Moon") by guiding you back to the current step
- Type `exit` at any time to say goodbye and quit
- Automatic fallback between several free models if one fails
- Bonus: simple web interface built with Streamlit

## Project structure

```
travelbuddy/
├── travelbuddy.py     # chatbot logic (steps, options, OpenRouter calls)
├── main.py            # console interface
├── app_web.py         # bonus: Streamlit web interface
├── list_free.py       # helper: prints the free models currently on OpenRouter
├── requirements.txt
├── .env.example       # template for your API key
└── README.md
```

## Setup

**Requirements:** Python 3.10+ and a free [OpenRouter](https://openrouter.ai/keys) API key.

1. Clone the repository and open the app folder:
```bash
   git clone https://github.com/EleneTser/TravelBuddy.git
   cd TravelBuddy/travelbuddy
```
2. Create and activate a virtual environment:
```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Mac/Linux:
   source .venv/bin/activate
```
3. Install the dependencies:
```bash
   pip install -r requirements.txt
```
4. Create your `.env` file from the template and add your key:
```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # Mac/Linux
```
   Then edit `.env`:
```
   OPENROUTER_API_KEY=your_key_here
```
   The `.env` file is listed in `.gitignore`, so your key is never committed.

## Run

**Console version:**
```bash
python main.py
```

**Web version (bonus):**
```bash
streamlit run app_web.py
```
Then open http://localhost:8501 in your browser.

Type `exit` in the console to quit.

## Example conversation

```
🧳 TravelBuddy (type 'exit' to quit)

TravelBuddy: Hey there! 🌟 I'm excited to help you plan an amazing weekend
getaway in just 3 quick steps: trip type, accommodation, and activities.
Which trip type sounds best for you?

1. Beach
2. Mountains
3. City break

You: I want to stay on the Moon

TravelBuddy: Ha, the Moon sounds out of this world! 🌙 Sadly I can't book
that one, but let's find you something just as dreamy. Please pick one:

1. Beach
2. Mountains
3. City break

You: 1

TravelBuddy: Beach it is — sun, sand and salty breezes await! 🌊☀️
Step 2: where would you like to rest your head?

1. Cozy guesthouse
2. Boutique hotel
3. Camping

You: 2

TravelBuddy: A boutique hotel for your beach getaway, fabulous! ✨🏨
Step 3: which activity sounds fun?

1. Snorkeling
2. Sunset sailing
3. Beach volleyball

You: 2

TravelBuddy: Your perfect weekend getaway is all set! 🥳

- Trip type: Beach
- Accommodation: Boutique hotel
- Activity: Sunset sailing 🌅

Type 'exit' whenever you're ready to leave.

You: exit

TravelBuddy: Safe travels, adventurer! 🌍✈️ Goodbye!
```

## Design decisions

**Python controls the flow, the LLM writes the words.**
Small, free language models are not reliable at remembering which step they are on. So the code keeps track of the current step and the user's choices, and decides which options are valid. The model is only asked to write the friendly wording for each step. This makes the bot hard to break.

**Conversation history is sent on every call.**
The full list of user and assistant messages is sent to the model each time, so it can refer to earlier choices. The chosen options are also stored in a dictionary in Python, so the final summary is always accurate.

**Activities depend on the trip type.**
A dictionary maps each trip type to its own activities, so suggestions always make sense (hiking for mountains, snorkeling for the beach).

**Unexpected answers never break the bot.**
If the answer does not match an option, the step does not advance. The bot politely explains that it can't arrange that and shows the same options again.

**Forgiving input.**
Users can answer with a number (`2`) or a name (`boutique`, `Boutique hotel`).

**Model choice and fallbacks.**
The assignment asks for `meta-llama/llama-3-8b-instruct`, but OpenRouter no longer serves it (the API returns a 404 saying so). Its paid successors also need credits, so the app uses free OpenRouter models instead, as the assignment allows. The free list changes often and free models can be rate-limited, so `travelbuddy.py` tries several models in order and moves to the next one if a request fails, returns an empty reply, or hits a rate limit. The last fallback is `openrouter/free`, which picks any available free model. `list_free.py` prints the currently free models so the list can be updated.

**Never crash.**
If every model fails, the bot shows a friendly static message instead of an error. Ctrl+C and end-of-input are also caught, so the program exits politely.

**Secrets stay out of Git.**
The API key lives in `.env`, which is ignored by Git. 

## Testing

I tested these cases by hand:

| Test | Expected result |
|---|---|
| `1`, `2`, `1` | Beach → Cozy guesthouse → Snorkeling, then a summary |
| `beach`, `boutique`, `sunset` | Names and partial names are accepted |
| `I want to stay on the Moon` | Bot stays on the same step and shows the options again |
| Mountains trip | Only hiking, biking and stargazing are offered |
| `exit` at any step | Goodbye message, program quits |
| Empty input | Ignored, the prompt appears again |
| Typing after the summary | Short cheerful reply, no restart |

## Known limitations

- Free models can be slow, rate-limited, or occasionally produce slightly odd wording. The step logic and the saved choices stay correct even then.
- Free models have daily request limits on OpenRouter.
