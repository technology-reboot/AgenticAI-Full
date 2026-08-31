"""
Lab: Single-agent Travel Planner with a Weather tool
Session 08 — Agentic AI Fundamentals

A single LangChain agent that:
  1. Reasons about a trip request
  2. Decides to call a weather tool for current conditions
  3. Feeds the forecast back and returns a grounded 2-day itinerary

Run:
    python travel_planner.py
"""

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# ----------------------------------------------------------------------------
# Secrets (Session 4's ChatModel setup — python-dotenv, fail loudly if missing)
# ----------------------------------------------------------------------------
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit(
        "OPENAI_API_KEY is not set. Add it to a .env file (see .env.example)."
    )


# ----------------------------------------------------------------------------
# Step 1 + 2: the weather tool
# ----------------------------------------------------------------------------
# Mock forecast table. Real weather APIs are rate-limited / paid, so the lab
# uses a deterministic mock the agent can still reason over. "Goa" is sunny;
# "Manchester" is rainy so we can watch the itinerary change.
_MOCK_FORECASTS = {
    "goa": {"condition": "sunny", "temp_c": 32},
    "manchester": {"condition": "rainy", "temp_c": 12},
    "reykjavik": {"condition": "snow", "temp_c": -2},
    "dubai": {"condition": "sunny", "temp_c": 40},
}


@tool
def get_weather(city: str) -> dict:
    """Return the current weather forecast for a city as {condition, temp_c}.

    Use this whenever a trip recommendation depends on current conditions.
    """
    return _MOCK_FORECASTS.get(
        city.strip().lower(),
        {"condition": "partly cloudy", "temp_c": 22},
    )


# ----------------------------------------------------------------------------
# Step 3: bind the tool to a ChatOpenAI model
# ----------------------------------------------------------------------------
# gpt-4o-mini + low temperature keeps the lab cheap to run repeatedly.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools([get_weather])

TOOLS_BY_NAME = {"get_weather": get_weather}

SYSTEM_PROMPT = (
    "You are a concise travel planner. When a request depends on current "
    "conditions, call the get_weather tool before answering. Then produce a "
    "day-by-day itinerary that visibly reflects the forecast: prefer indoor "
    "activities when it is rainy or snowy, outdoor activities when it is sunny."
)


def plan_trip(request: str) -> str:
    """Run one reason -> tool-call -> observe -> answer cycle for a trip request."""
    print("\n" + "=" * 80)
    print(f"REQUEST: {request}")
    print("=" * 80)

    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(request)]

    # Step 4: first model turn — inspect tool_calls BEFORE executing them.
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    print("\n--- Model's tool_calls (chosen before any execution) ---")
    if not ai_msg.tool_calls:
        print("(none — the model answered directly)")
        print("\n--- Itinerary ---")
        print(ai_msg.content)
        return ai_msg.content

    for call in ai_msg.tool_calls:
        print(f"  {call['name']}(args={call['args']})  id={call['id']}")

    # Step 5: execute each tool call and feed the result back.
    for call in ai_msg.tool_calls:
        result = TOOLS_BY_NAME[call["name"]].invoke(call["args"])
        print(f"\n  -> {call['name']} returned: {result}")
        messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    final_msg = llm_with_tools.invoke(messages)
    print("\n--- Itinerary (grounded in the forecast) ---")
    print(final_msg.content)
    return final_msg.content


# ----------------------------------------------------------------------------
# Step 4 + 6: run the base prompt, then a rainy-city contrast test
# ----------------------------------------------------------------------------
def main() -> None:
    plan_trip("Plan a 2-day trip to Goa")
    plan_trip("Plan a 2-day trip to Manchester")


if __name__ == "__main__":
    main()
