import os
from langchain.chat_models import init_chat_model


def get_model():
    """Return a configured LLM instance.

    Automatically picks the provider based on which API key is set in .env.
    Priority: Google Gemini → OpenAI → Anthropic

    To switch providers, just change your .env key and update the model name below.
    """

    if os.getenv("GOOGLE_API_KEY"):
        return init_chat_model(
            "gemini-2.5-flash",
            model_provider="google-genai",
            temperature=0.5,
            max_tokens=8000,
            streaming=True,
        )

    if os.getenv("OPENAI_API_KEY"):
        return init_chat_model(
            "gpt-4o-mini",
            model_provider="openai",
            temperature=0.5,
            max_tokens=8000,
            streaming=True,
        )

    if os.getenv("ANTHROPIC_API_KEY"):
        return init_chat_model(
            "claude-sonnet-4-6",
            model_provider="anthropic",
            temperature=0.5,
            max_tokens=8000,
            streaming=True,
        )

    raise EnvironmentError(
        "No API key found. Please set GOOGLE_API_KEY, OPENAI_API_KEY, or "
        "ANTHROPIC_API_KEY in your .env file."
    )
