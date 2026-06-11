# BUFFER MEMORY AGENT
import os
import random

HISTORY_FILE = "chat_history.txt"
history = []  # BUFFER MEMORY

# Simple bot replies
responses = [
    "Interesting! Tell me more 🤔",
    "Acha acha, samajh gaya! 😄",
    "Wah Sensei, kya baat hai! 🔥",
    "Hmm, soch raha hoon... 🤖",
    "Bilkul sahi kaha! 👍",
]

# Load existing history into buffer on startup
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        history = file.read().splitlines()

print("==Buffer Memory Agent==")
print("Type 'history' to view history")
print("Type 'exit' to exit\n")

while True:
    user_ip = input("You: ")

    # EXIT
    if user_ip.lower() == "exit":
        print("Bot: Sayonara Sensei 🫡🫂")
        break

    # HISTORY
    elif user_ip.lower() == "history":
        if len(history) == 0:
            print("------->>> SENSEI THERE IS NOTHING IN THE FILE, WE HAVEN'T TALKED YET 🙁\n")
        else:
            print("\n--- History ---")
            for msg in history:
                print(msg)
            print("---------------\n")

    # SAVE TO BUFFER + FILE
    else:
        bot_reply = random.choice(responses)  # Bot picks a random reply

        # Save both in buffer
        history.append(f"You: {user_ip}")
        history.append(f"Bot: {bot_reply}")

        print(f"Bot: {bot_reply}")
        print("<-- Sensei save ho gya -->\n")

        # Save both in file
        with open(HISTORY_FILE, "a", encoding="utf-8") as file:
            file.write(f"You: {user_ip}\n")
            file.write(f"Bot: {bot_reply}\n")