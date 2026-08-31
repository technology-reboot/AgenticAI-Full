"""Lab 3 — simple tool design patterns.

This file demonstrates the idea of a tool registry and a small tool execution loop.
The training goal is to show that tools can be wrapped behind a consistent interface.
"""

from __future__ import annotations

from typing import Callable, Dict, List


class ToolRegistry:
    """A tiny registry that stores named tools and executes them."""

    def __init__(self) -> None:
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    def run(self, tool_name: str, **kwargs) -> dict:
        if tool_name not in self._tools:
            return {"error": f"Unknown tool: {tool_name}"}
        return self._tools[tool_name](**kwargs)


# -----------------------------------------------------------------------------
# Example tools
# -----------------------------------------------------------------------------
def search_knowledge_base(query: str) -> dict:
    """Return a simple knowledge-base result for a query."""
    return {"result": f"Knowledge base match for: {query}"}


def summarize_ticket(ticket_text: str) -> dict:
    """Create a short summary from a ticket text."""
    return {"summary": ticket_text[:80] + ("..." if len(ticket_text) > 80 else "")}


def classify_priority(priority: str) -> dict:
    """Map a rough priority label to a queue."""
    mapping = {
        "high": "P1",
        "medium": "P2",
        "low": "P3",
    }
    return {"queue": mapping.get(priority.lower(), "P3")}


def main() -> None:
    """Show tool registration and execution."""
    registry = ToolRegistry()
    registry.register("search_knowledge_base", search_knowledge_base)
    registry.register("summarize_ticket", summarize_ticket)
    registry.register("classify_priority", classify_priority)

    print("Registered tools:")
    for name in registry._tools:
        print(f"- {name}")

    print("\nRunning sample tool calls:")
    print(registry.run("summarize_ticket", ticket_text="My app is slow and I need help."))
    print(registry.run("classify_priority", priority="high"))
    print(registry.run("search_knowledge_base", query="mobile app slow"))


if __name__ == "__main__":
    main()
