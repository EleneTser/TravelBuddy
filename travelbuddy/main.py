# Import the chatbot class from travelbuddy.py
from travelbuddy import TravelBuddy


def main():
    # Create one chatbot (it keeps the chat history and the user's choices)
    bot = TravelBuddy()

    print("\n🧳 TravelBuddy (type 'exit' to quit)\n")

    # The bot speaks first: greeting + the first question
    print(f"TravelBuddy: {bot.start()}\n")

    try:
        # Keep chatting until the user types "exit"
        while True:
            user = input("You: ").strip()

            # If the user just pressed Enter, ask again
            if not user:
                continue

            # Say goodbye and stop the loop
            if user.lower() == "exit":
                print(
                    "\nTravelBuddy: Safe travels, adventurer! "
                    "🌍✈️ Goodbye!"
                )
                break

            # Send the answer to the bot and print its reply
            print(f"\nTravelBuddy: {bot.respond(user)}\n")

    # If the user presses Ctrl+C (or input ends), exit politely
    # instead of showing a scary error message.
    except (KeyboardInterrupt, EOFError):
        print("\n\nTravelBuddy: Safe travels! 🌍✈️ Goodbye!")


# Run main() only when this file is started directly (python main.py)
if __name__ == "__main__":
    main()