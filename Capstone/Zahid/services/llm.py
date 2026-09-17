import os
from typing import Any

from dotenv import load_dotenv


def create_advisory_llm() -> Any | None:
    """Create the optional OpenAI model; deterministic services work without it."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)