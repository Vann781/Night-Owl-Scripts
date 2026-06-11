# ENTITY MEMORY AGENT 🗂️
# Remembers specific facts about named entities (people, places, things)
# Updates existing entity facts instead of repeating them

import os
import json
import random

ENTITY_FILE = "entity_memory.json"

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
# ENTITY DETECTION RULES
# Simple keyword-based entity extractor
# Format: "ENTITY_NAME is/likes/has/lives FACT"
# ───────────────────────────────────────────
TRIGGER_WORDS = ["is", "likes", "loves", "hates", "has", "lives", "works", "plays", "wants", "eats"]

def extract_entity(user_input):
    """
    Tries to extract (entity_name, attribute, value) from user input.

    Examples:
      "Henry likes pizza"       → ("Henry", "likes", "pizza")
      "Peter is a good student" → ("Peter", "is", "a good student")
      "Mum lives in London"     → ("Mum", "lives", "London")

    Returns None if no pattern is found.
    """
    words = user_input.strip().split()
    for i, word in enumerate(words):
        if word.lower() in TRIGGER_WORDS and i > 0:
            entity = " ".join(words[:i]).strip()          # words before trigger
            attribute = word.lower()                       # the trigger word itself
            value = " ".join(words[i+1:]).strip()         # words after trigger
            if entity and value:
                return entity, attribute, value
    return None

# ───────────────────────────────────────────
# ENTITY MEMORY FUNCTIONS
# ───────────────────────────────────────────
def load_entities():
    """Load entity memory from JSON file."""
    if os.path.exists(ENTITY_FILE):
        with open(ENTITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_entities(entities):
    """Save entity memory to JSON file."""
    with open(ENTITY_FILE, "w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)

def update_entity(entities, entity_name, attribute, value):
    """
    Add or update a fact about an entity.
    Each entity is a dict of {attribute: value}.
    """
    key = entity_name.lower()  # normalize to lowercase key
    if key not in entities:
        entities[key] = {"_display_name": entity_name}  # preserve original casing

    entities[key][attribute] = value
    return entities

def recall_entity(entities, entity_name):
    """Return all known facts about an entity, or None if unknown."""
    key = entity_name.lower()
    return entities.get(key, None)

def format_entity(facts):
    """Format entity facts for display."""
    display = facts.get("_display_name", "Unknown")
    lines = [f"  Entity: {display}"]
    for attr, val in facts.items():
        if attr != "_display_name":
            lines.append(f"    {attr}: {val}")
    return "\n".join(lines)

# ───────────────────────────────────────────
# MAIN AGENT
# ───────────────────────────────────────────
entity_memory = load_entities()

print("==Entity Memory Agent==")
print("I remember facts about named people & things!")
print()
print("Try saying:")
print("  'Henry likes pizza'")
print("  'Peter is a good student'")
print("  'Mum works at a hospital'")
print()
print("Type 'who is NAME'  → Recall facts about someone")
print("Type 'entities'     → List all known entities")
print("Type 'forget NAME'  → Remove an entity")
print("Type 'clear'        → Clear all entity memory")
print("Type 'exit'         → Bahar jaao\n")

while True:
    user_ip = input("You: ")

    # EXIT
    if user_ip.lower() == "exit":
        print("Bot: Sayonara Sensei! Sab yaad rakhoon ga! 🗂️")
        break

    # RECALL: "who is NAME"
    elif user_ip.lower().startswith("who is "):
        name = user_ip[7:].strip()
        facts = recall_entity(entity_memory, name)
        if facts:
            print(f"\n--- I know about {name}! ---")
            print(format_entity(facts))
            print()
        else:
            print(f"Bot: '{name}' ke baare mein mujhe kuch nahi pata! Kuch batao inke baare mein 🤔\n")

    # LIST ALL ENTITIES
    elif user_ip.lower() == "entities":
        if not entity_memory:
            print("------->>> Koi entity yaad nahi hai abhi tak! 🙁\n")
        else:
            print(f"\n--- All Known Entities ({len(entity_memory)} total) ---")
            for key, facts in entity_memory.items():
                print(format_entity(facts))
                print()

    # FORGET ONE ENTITY
    elif user_ip.lower().startswith("forget "):
        name = user_ip[7:].strip()
        key = name.lower()
        if key in entity_memory:
            del entity_memory[key]
            save_entities(entity_memory)
            print(f"Bot: '{name}' ko bhool gaya! 🗑️\n")
        else:
            print(f"Bot: '{name}' toh kabhi yaad hi nahi tha! 🤷\n")

    # CLEAR ALL
    elif user_ip.lower() == "clear":
        entity_memory = {}
        if os.path.exists(ENTITY_FILE):
            os.remove(ENTITY_FILE)
        print("Bot: Saari yaadein saaf! Fresh start! 🧹\n")

    # NORMAL CHAT — try to extract an entity fact
    else:
        bot_reply = random.choice(responses)
        extracted = extract_entity(user_ip)

        if extracted:
            entity_name, attribute, value = extracted
            entity_memory = update_entity(entity_memory, entity_name, attribute, value)
            save_entities(entity_memory)

            print(f"Bot: {bot_reply}")
            print(f"<-- Entity saved: [{entity_name}] → [{attribute}: {value}] -->\n")
        else:
            print(f"Bot: {bot_reply}")
            print("<-- No entity detected in this message -->\n")