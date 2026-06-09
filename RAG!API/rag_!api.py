import os
import re
from transformers import pipeline

# ==========================================
# 1. THE KNOWLEDGE BASE (Our Local Data)
# ==========================================
# A simple mock database of private/local information the LLM wouldn't know normally.
LOCAL_DATABASE = {
    "hackathon": "The campus Hackathon 2.0: AI Odyssey is scheduled for March 2026, focusing on multi-agent frameworks.",
    "hunter system": "Project 'Hunter's System' is a gamified fitness application that tracks workout milestones using anime-inspired rank advancements.",
    "flutter deployment": "To build an optimized release APK in Flutter, use the command: 'flutter build apk --split-per-abi'.",
    "backend auth": "The Node.js Express template uses JWT tokens stored in HTTP-only cookies for secure session management."
}

def tool_search_database(query: str) -> str:
    """A basic keyword-matching retrieval tool representing our RAG component."""
    query = query.lower()
    matches = []
    for key, content in LOCAL_DATABASE.items():
        if key in query or any(word in query for word in key.split()):
            matches.append(f"[{key}]: {content}")
    
    return "\n".join(matches) if matches else "No relevant documents found in the database."


# ==========================================
# 2. INITIALIZE THE LOCAL LLM
# ==========================================
print("🔄 Loading local LLM (Qwen2.5-0.5B-Instruct)... This might take a moment on the first run.")
# We use a 0.5 Billion parameter model. It's tiny, fast on CPU, and shockingly good at instructions.
agent_llm = pipeline(
    "text-generation", 
    model="Qwen/Qwen2.5-0.5B-Instruct", 
    max_new_tokens=150,
    temperature=0.1 # Low temperature keeps the agent structured and stable
)


# ==========================================
# 3. THE AGENT PROMPT & LOGIC
# ==========================================
SYSTEM_PROMPT = """
You are a smart AI Agent with access to a specific local database tool.
Your available tool is: search_database(query="keyword")

When the user asks a question, you must think if you need to look up info in the database or if you can answer it accurately from general knowledge.

You MUST respond exactly in one of these two formats. Do not add anything else.

Format 1 (If you need to search):
THOUGHT: I need to look up specific project or event details.
ACTION: search_database(query="put keyword here")

Format 2 (If you have enough info to answer directly):
THOUGHT: I know the answer directly.
RESPONSE: [Your final helpful answer here]
"""

def run_agentic_rag(user_query: str):
    print(f"\n👤 User: {user_query}")
    
    # Construct the message sequence
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    # --- TURN 1: Agent Reasonings ---
    outputs = agent_llm(messages)
    agent_response = outputs[0]['generated_text'][-1]['content']
    print(f"🤖 Agent Internal Processing:\n{agent_response.strip()}")
    
    # Check if the agent decided to use the tool
    action_match = re.search(r'ACTION:\s*search_database\(query=["\'](.*?)["\']\)', agent_response)
    
    if action_match:
        search_keyword = action_match.group(1)
        print(f"🛠️ [Executing Tool] Searching database for: '{search_keyword}'")
        
        # Run the RAG tool
        tool_result = tool_search_database(search_keyword)
        print(f"📦 [Tool Output] Found: {tool_result}")
        
        # --- TURN 2: Provide the tool data back to the Agent ---
        # We append the agent's thought process and the tool result to the conversation history
        messages.append({"role": "assistant", "content": agent_response})
        messages.append({
            "role": "user", 
            "content": f"TOOL RESULT: {tool_result}\n\nNow, provide your final response using this data."
        })
        
        final_outputs = agent_llm(messages)
        final_answer = final_outputs[0]['generated_text'][-1]['content']
        
        # Clean up any leftover 'RESPONSE:' tags if the model generated them
        clean_answer = final_answer.replace("RESPONSE:", "").strip()
        print(f"\n🎯 Final Agent Answer:\n{clean_answer}")
    else:
        # The agent answered directly without needing the tool
        clean_answer = agent_response.split("RESPONSE:")[-1].strip()
        print(f"\n🎯 Final Agent Answer:\n{clean_answer}")

# ==========================================
# 4. RUNNING TEST CASES
# ==========================================
if __name__ == "__main__":
    # Test Case A: Requires RAG Tool
    run_agentic_rag("What is the command to build an optimized APK in Flutter?")
    
    print("\n" + "="*50 + "\n")
    
    # Test Case B: General knowledge (Should bypass the tool)
    run_agentic_rag("What is the capital of France?")