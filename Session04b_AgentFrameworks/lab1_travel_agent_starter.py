# Lab 1 — Single agent: travel planner with a live weather tool  (STARTER)
#
# Fill in the four TODO blocks below. The rest of the file is done for you.
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
    # TODO (1/4): implement the tool body.
    #  - if BREAK_TOOL is True, raise RuntimeError immediately (no API call)
    #  - else GET https://api.openweathermap.org/data/2.5/weather with params
    #    q=city, units=metric, appid=OPENWEATHER_API_KEY, and timeout=10
    #  - on a network error or a non-200 response, RETURN a clear error string
    #    like f"Weather lookup failed for {city}: {reason}" (do not raise)
    #  - on success, return f"{description}, {temp:.1f}C, feels like {feels:.1f}C"
    raise NotImplementedError


SYSTEM_PROMPT = (
    "You are a travel planning assistant. You help people plan short trips. "
    "Before giving any advice about packing or the timing of a trip, check the "
    "current weather with the get_weather tool. For general questions that do "
    "not depend on current conditions, answer directly without any tool."
)

# TODO (2/4): build the agent.
#  Use create_agent(...) from langchain.agents with:
#    - a ChatOpenAI model, model="gpt-4o-mini", temperature=0
#    - tools=[get_weather]
#    - system_prompt=SYSTEM_PROMPT
#  Do NOT use create_react_agent, AgentExecutor, or initialize_agent.
agent = None


def _one_line(text: str, limit: int = 100) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def print_trace(messages) -> None:
    # TODO (3/4): print one compact line per message.
    #  - iterate messages; branch on msg.type ("human" / "ai" / "tool")
    #  - for an "ai" message, print each entry of msg.tool_calls as
    #      [ai]        -> tool_call: get_weather({'city': 'Pune'})
    #    and, if msg.content is non-empty, print it on an [ai] line
    #  - for a "tool" message print: [tool]  <msg.name> -> "<truncated content>"
    #  - print tool name and arguments, never a raw object dump
    print("--- trace ---")
    raise NotImplementedError


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
    # TODO (4/4): set BREAK_TOOL = True, then call run_scenario(...) a third time
    #  with the SCENARIO 3 banner and the same Pune raincoat question.


main()
