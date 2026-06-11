"""
Entry point for the agent.

Usage:
    python main.py                     # interactive chat loop
    python main.py "your question"     # single question mode
"""

import sys
from dotenv import load_dotenv

load_dotenv()  # loads keys from .env before anything else

from deepagents import create_deep_agent
from agent import get_model, get_tools, SYSTEM_PROMPT, get_checkpointer


def build_agent():
    return create_deep_agent(
        model=get_model(),
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=get_checkpointer(),
    )


def ask(agent, question: str, thread_id: str = "default") -> str:
    """Send a message to the agent and return the response text."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    blocks = result["messages"][-1].content_blocks
    # content_blocks can be a list of dicts or a plain string depending on the model
    if isinstance(blocks, str):
        return blocks
    return " ".join(
        b.get("text", "") if isinstance(b, dict) else str(b) for b in blocks
    ).strip()


def interactive_loop(agent):
    """Simple REPL — type a message, get a response. Ctrl+C or 'exit' to quit."""
    print("Agent ready. Type your message (or 'exit' to quit).\n")
    thread_id = "interactive-session"
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        if not user_input or user_input.lower() in {"exit", "quit"}:
            print("Bye!")
            break
        response = ask(agent, user_input, thread_id=thread_id)
        print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    agent = build_agent()

    if len(sys.argv) > 1:
        # Single question mode: python main.py "what is the weather in Delhi?"
        question = " ".join(sys.argv[1:])
        print(ask(agent, question))
    else:
        # Interactive chat loop
        interactive_loop(agent)
