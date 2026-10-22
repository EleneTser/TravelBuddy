from travelbuddy import TravelBuddy


def main():
    bot = TravelBuddy()
    print("\n🧳 TravelBuddy (type 'exit' to quit)\n")
    print(f"TravelBuddy: {bot.start()}\n")

    while True:
        user = input("You: ").strip()
        if not user:
            continue
        if user.lower() == "exit":
            print("\nTravelBuddy: Safe travels, adventurer! 🌍✈️ Goodbye!")
            break
        print(f"\nTravelBuddy: {bot.respond(user)}\n")


if __name__ == "__main__":
    main()