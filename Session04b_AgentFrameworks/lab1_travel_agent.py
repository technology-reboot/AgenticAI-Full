# Lab 1 — Single agent: travel planner with a live weather tool
#
# Instructor notes:
# - The docstring is the tool's contract with the model. Delete it and the agent
#   stops choosing the tool correctly — worth demonstrating live if there is time.
# - If a student's agent calls the weather tool for the Goa question, their system
#   prompt is over-instructing. Good discussion point.
# - The broken-tool scenario is the seed for FM-2 (tool failure handled as fact)
#   in the Agent Evaluation session. Tell students to keep their observation.

import os

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

load_dotenv()


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise SystemExit(f"Missing {var} — add it to .env and re-run.")
    return value


OPENAI_API_KEY = _require("OPENAI_API_KEY")
OPENWEATHER_API_KEY = _require("OPENWEATHER_API_KEY")

# Flip to True for SCENARIO 3 — see the comment block above that scenario.
BREAK_TOOL = False


# The text below is not documentation for humans — it is what the model reads
# when it decides whether to call this tool and what to pass as `city`.
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city. Call this before giving any packing or
    timing advice that depends on current conditions. Pass the plain city name,
    e.g. "Pune". Returns a short description with temperature in Celsius."""
    if BREAK_TOOL:
        raise RuntimeError("Weather service unavailable (BREAK_TOOL is on)")

    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "units": "metric", "appid": OPENWEATHER_API_KEY},
            timeout=10,
        )
    except requests.RequestException as exc:
        return f"Weather lookup failed for {city}: {exc}"

    if resp.status_code != 200:
        reason = resp.json().get("message", resp.reason)
        return f"Weather lookup failed for {city}: {reason}"

    data = resp.json()
    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    return f"{desc}, {temp:.1f}C, feels like {feels:.1f}C"


SYSTEM_PROMPT = (
    "You are a travel planning assistant. You help people plan short trips. "
    "Before giving any advice about packing or the timing of a trip, check the "
    "current weather with the get_weather tool. For general questions that do "
    "not depend on current conditions, answer directly without any tool."
)

agent = create_agent(
    ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=[get_weather],
    system_prompt=SYSTEM_PROMPT,
)


def _one_line(text: str, limit: int = 100) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def print_trace(messages) -> None:
    print("--- trace ---")
    for msg in messages:
        kind = msg.type
        if kind == "human":
            print(f"[human]     {_one_line(msg.content)}")
        elif kind == "ai":
            for call in msg.tool_calls:
                print(f"[ai]        -> tool_call: {call['name']}({call['args']})")
            if msg.content:
                print(f"[ai]        {_one_line(msg.content)}")
        elif kind == "tool":
            print(f'[tool]      {msg.name} -> "{_one_line(msg.content, 80)}"')


def run_scenario(banner: str, question: str) -> None:
    print("\n" + "=" * 66)
    print(f" {banner}")
    print("=" * 66)
    print(f"Question: {question}\n")

    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    messages = result["messages"]

    print_trace(messages)

    tool_calls = sum(len(m.tool_calls) for m in messages if m.type == "ai")
    print(f"\nFinal answer:\n{messages[-1].content}")
    print(f"\nTool calls: {tool_calls}")


def main() -> None:
    global BREAK_TOOL

    run_scenario("SCENARIO 1 — question that needs the tool",
                 "Should I pack a raincoat for Pune this week?")

    run_scenario("SCENARIO 2 — question that does not need the tool",
                 "What is a good time of year to visit Goa?")

    # SCENARIO 3 — the weather tool is broken and raises on every call.
    # Watch the trace and the final answer, and record ONE observation:
    #   does the agent retry the tool, report the failure honestly to the user,
    #   or answer from its own knowledge as if the tool had returned data?
    BREAK_TOOL = True
    run_scenario("SCENARIO 3 — tool deliberately broken",
                 "Should I pack a raincoat for Pune this week?")


main()
