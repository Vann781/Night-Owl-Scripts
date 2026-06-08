from gtts import gTTS
from playsound import playsound
import random
import os
import time

# ===============================
# AI Motivation Agent using TTS
# ===============================

motivations = [
    "Wake up warrior. Your dreams are waiting.",
    "Discipline beats motivation every single time.",
    "The grind you avoid today becomes regret tomorrow.",
    "Legends are built in silence.",
    "LOCK IN BRO. SUCCESS NEEDS SACRIFICE.",
    "Every small step matters.",
    "Nobody is coming to save you. Build yourself.",
    "One more hour today changes your future."
]

# Clear screen
os.system("cls")

print("=" * 50)
print("🔥 AI MOTIVATION AGENT 🔥")
print("=" * 50)

# User input
name = input("\n👤 Enter your name: ")

goal = input("🎯 What is your goal? ")

hours = input("⏳ Study hours today: ")

print("\n🤖 AI Thinking", end="")

for i in range(5):
    time.sleep(0.5)
    print(".", end="")

print("\n")

# Generate message
message = random.choice(motivations)

final_message = f"""
{name},
your goal is {goal}.

You planned to study for {hours} hours today.

{message}
"""

# Print message
print("=" * 50)
print(final_message)
print("=" * 50)

# ==================================
# TEXT TO SPEECH
# ==================================

tts = gTTS(text=final_message, lang='en')

tts.save("motivation.mp3")

playsound("motivation.mp3")

# Delete audio after playing
os.remove("motivation.mp3")

print("\n🔥 Keep grinding warrior.")

input("\nPress Enter to exit...")

