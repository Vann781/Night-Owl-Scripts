import urllib.request
import urllib.error
from langchain.tools import tool


@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch the full plain-text content of a public URL.

    Use this to load documents, articles, or any web page the user references.
    Returns the raw text content, or an error message if the fetch fails.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; my-agent/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
        return raw.decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Returns a short weather summary for the requested city.
    (This is a mock tool — replace with a real weather API call in production.)
    """
    # Replace this with a real API call, e.g. OpenWeatherMap
    return f"It's currently sunny and 24°C in {city}. No rain expected today."


def get_tools():
    """Return the list of tools available to the agent."""
    return [fetch_text_from_url, get_weather]
