import os
import json
import requests
from pathlib import Path
from typing import Any, Dict, Tuple
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI
 
PROJECT_ROOT = Path(__file__).resolve().parent
 
def load_environment() -> Dict[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    return {key: os.getenv(key, "") for key in
            ["AZURE_OPENAI_ENDPOINT",
             "AZURE_OPENAI_API_KEY",
             "AZURE_OPENAI_DEPLOYMENT",
             "OPENWEATHER_API_KEY",
             ]}
 
def get_clients() -> Tuple[AzureOpenAI, AsyncAzureOpenAI, str, str]:
    env = load_environment()
    endpoint = env["AZURE_OPENAI_ENDPOINT"]
    api_key = env["AZURE_OPENAI_API_KEY"]
 
    if not endpoint or not api_key:
        raise RuntimeError(
            "Credentials/Keys are missing"
        )
 
    deployment = env["AZURE_OPENAI_DEPLOYMENT"] = "gpt-4.1-mini"
 
    sync_client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2025-01-01-preview"
    )
 
    async_client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2025-01-01-preview"
    )
    return sync_client, async_client, deployment, ""
 
 
def _weather_api_key() -> str:
    return os.getenv("OPENWEATHER_API_KEY", "")
 
TRAVEL_INTENT = {"destination": "Rajasthan", "duration_days": 5, "travel_month": "February", "group_type": "family", "preferences": ["heritage sites", "local food markets"], "accommodation_preference": "heritage hotels or havelis", "budget_inr": 200000}
 
INSTRUCTIONS = "You are a travel planning agent. Always call get_weather first for the destination and travel month, then build a day-by-day itinerary that aligns outdoor activities with the good weather windows. Respond with valid JSON only, using keys: destination, duration_days, weather_summary, packing_essentials, itinerary, estimated_cost_inr, travel_tips."
 
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Look up the near-term weather forecast for a destination. Returns a JSON string with average, min and max temperature plus the expected conditions so the itinerary can be aligned to good weather windows and packing advice.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "City or region to look up."},
                "travel_month": {"type": "string", "description": "Month of travel, e.g. February."},
            },
            "required": ["destination", "travel_month"],
        },
    },
}
 
def get_weather(destination:str, travel_month:str) -> str:
    api_key = _weather_api_key()
    try:
        geo = requests.get("https://api.openweathermap.org/geo/1.0/direct",
                            params = {"q": destination, "limit" : 1, "appid": api_key},  timeout=10).json()
        if not geo:
            return json.dumps({"destination": destination, "error": "location not found"})
        forecast = requests.get("https://api.openweathermap.org/data/2.5/forecast",
                                params = {"lat": geo[0]["lat"], "lon": geo[0]["lon"], "cnt": 4, "appid": api_key, "units": "metric"}, timeout=10).json()
        temps = [entry["main"]["temp"] for entry in forecast.get("list", [])]
        conditions = sorted({entry["weather"][0]["description"] for entry in forecast.get("list",[])})
        return json.dumps({"destination": destination, "travel_month": travel_month, "avg_temp_celsius": round(sum(temps) / len(temps), 1) if temps else None, "min_temp_celsius": min(temps) if temps else None, "max_temp_celsius": max(temps) if temps else None, "conditions": conditions, "source": "OpenWeather 5-day / 3-hour forecast"})
    except Exception as e:
        return json.dumps({"destination": destination, "error": str(e)})
 
 
def run_agent(client, deployment:str, travel_intent: dict) -> dict:
    messages = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": json.dumps(travel_intent)},
    ]
 
    for _ in range(5):
        response = client.chat.completions.create(
            model = deployment,
            messages = messages,
            tools = [WEATHER_TOOL],
            temperature = 0.0,
            max_tokens = 1200,
            response_format = {"type" : "json_object"}
        )
        message = response.choices[0].message
 
        if not message.tool_calls:
            return json.loads(message.content)

        messages.append({
            "role" : "assistant",
            "content" : message.content,
             "tool_calls" : [
                {"id" : call.id, "type": "function", "function": {"name": call.function.name, "arguments" : call.function.arguments}}
                for call in message.tool_calls
            ]
        })

        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            print(f" Tool call : get_weather({args})")
            result = get_weather(args.get("destination", ""), args.get("travel_month", ""))
            messages.append({"role": "tool", "tool_call_id": call.id, "content" : result})

    raise RuntimeError("Agent did not produce a final answer within the run limit")
 
def run_lab() -> None:
    print("Trip Planned + Weather tool agent")
    client, _, deployment, _ = get_clients()
    print("Azure Sync Client is ready")
    plan = run_agent(client, deployment, TRAVEL_INTENT)
    print("\n Agent Response")
    # print (plan)
    print(json.dumps(plan, indent=2))
 
 
if __name__ == "__main__":
    run_lab()