# WINDOW MEMORY AGENT 🪟
# Keeps only the last N messages (sliding window)
# Older messages are automatically dropped to save space

import os
import random

HISTORY_FILE = "window_history.txt"
WINDOW_SIZE = 6  # Max messages to keep (each exchange = 2: You + Bot)

# Simple bot replies
responses = [
    "Interesting! Tell me more 🤔",
    "Acha acha, samajh gaya! 😄",
    "Wah Sensei, kya baat hai! 🔥",
    "Hmm, soch raha hoon... 🤖",
    "Bilkul sahi kaha! 👍",
    "Kya baat hai, mast idea! 🌟",
]

# ───────────────────────────────────────────
# WINDOW MEMORY FUNCTIONS
# ───────────────────────────────────────────
def load_window():
    """Load existing messages from file into window buffer."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        # Only keep the last WINDOW_SIZE lines even on load
        return lines[-WINDOW_SIZE:]
    return []

def save_window(window):
    """Overwrite the file with only the current window."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(window) + "\n")

def add_to_window(window, user_msg, bot_msg):
    """Add new exchange and slide the window if it exceeds WINDOW_SIZE."""
    window.append(f"You: {user_msg}")
    window.append(f"Bot: {bot_msg}")

    # Slide: drop oldest messages if window is too large
    if len(window) > WINDOW_SIZE:
        dropped = len(window) - WINDOW_SIZE
        window = window[dropped:]
        print(f"  [Window slid: {dropped} old message(s) dropped]\n")

    return window

# ───────────────────────────────────────────
# MAIN AGENT
# ───────────────────────────────────────────
window_memory = load_window()

print("==Window Memory Agent==")
print(f"Window size: last {WINDOW_SIZE} messages only")
print("Type 'window'  → See current window")
print("Type 'size N'  → Change window size (e.g. 'size 4')")
print("Type 'clear'   → Clear window memory")
print("Type 'exit'    → Bahar jaao\n")

while True:
    user_ip = input("You: ")

    # EXIT
    if user_ip.lower() == "exit":
        print("Bot: Sayonara Sensei! Window band ho gayi! 🪟")
        break

    # SHOW CURRENT WINDOW
    elif user_ip.lower() == "window":
        if len(window_memory) == 0:
            print("------->>> Window khali hai! Abhi tak koi baat nahi hui 🙁\n")
        else:
            print(f"\n--- Current Window (last {WINDOW_SIZE} messages) ---")
            for msg in window_memory:
                print(msg)
            print(f"--- [{len(window_memory)}/{WINDOW_SIZE} slots used] ---\n")

    # CHANGE WINDOW SIZE
    elif user_ip.lower().startswith("size "):
        try:
            new_size = int(user_ip.split()[1])
            if new_size < 2:
                print("Bot: Minimum window size 2 honi chahiye! 🙅\n")
            else:
                WINDOW_SIZE = new_size
                # Re-trim existing window to new size
                if len(window_memory) > WINDOW_SIZE:
                    window_memory = window_memory[-WINDOW_SIZE:]
                print(f"Bot: Window size ab {WINDOW_SIZE} ho gayi! ✅\n")
        except ValueError:
            print("Bot: Sahi number dalo! Example: 'size 4' 🤔\n")

    # CLEAR WINDOW
    elif user_ip.lower() == "clear":
        window_memory = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        print("Bot: Window saaf ho gayi! Fresh start! 🧹\n")

    # NORMAL CHAT
    else:
        bot_reply = random.choice(responses)
        window_memory = add_to_window(window_memory, user_ip, bot_reply)
        save_window(window_memory)

        print(f"Bot: {bot_reply}")
        print(f"<-- Window updated: {len(window_memory)}/{WINDOW_SIZE} slots used -->\n")