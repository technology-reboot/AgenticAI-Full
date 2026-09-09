"""Lab 3: Orchestrator + simple deployment style example.

This script brings the earlier pieces together under an orchestrator flow:
1. Detect the input type
2. Route the request to the right agents
3. Build a final travel plan response
4. Print a simple summary that would be suitable for a training demo

The code is built for clarity rather than production complexity.
"""

import asyncio
from typing import Any, Dict, Optional

from common import demo_itinerary, demo_travel_intent, demo_vision_result, demo_weather, pretty_print_json


class OrchestratorState(Dict[str, Any]):
    """A small typed dictionary used for the training example."""


def detect_modality(state: OrchestratorState) -> str:
    """Simplify the input mode to text, audio, or multimodal."""
    if state.get("audio_path"):
        return "audio"
    if state.get("image_path") and state.get("raw_text_input"):
        return "multimodal"
    if state.get("raw_text_input"):
        return "text"
    raise ValueError("No valid input provided")


async def orchestrator(state: OrchestratorState) -> OrchestratorState:
    """Coordinate the flow and create a final response."""
    modality = detect_modality(state)
    processing_log = [f"Detected modality: {modality}"]

    # 1) Build the travel intent
    if modality == "text":
        processing_log.append("Processing text input directly.")
        travel_intent = demo_travel_intent()
    elif modality == "audio":
        processing_log.append("Treating input as audio and extracting intent from the transcript.")
        travel_intent = demo_travel_intent()
    else:
        processing_log.append("Image + text input detected; using vision context.")
        travel_intent = demo_travel_intent()

    # 2) Create itinerary and weather in parallel
    processing_log.append("Dispatching Trip Planner + Weather agents in parallel.")
    itinerary, weather = await asyncio.gather(
        asyncio.sleep(0, result=demo_itinerary()),
        asyncio.sleep(0, result=demo_weather()),
    )

    # 3) Assemble the final response
    vision_result = demo_vision_result() if modality == "multimodal" else None
    final_response = build_final_response(travel_intent, itinerary, weather, vision_result)
    processing_log.append("Final response assembled.")

    return {
        **state,
        "input_type": modality,
        "travel_intent": travel_intent,
        "hotel_vision_result": vision_result,
        "itinerary": itinerary,
        "weather": weather,
        "final_response": final_response,
        "processing_log": processing_log,
    }


def build_final_response(travel_intent: Dict[str, Any], itinerary: Dict[str, Any], weather: Dict[str, Any], vision_result: Optional[Dict[str, Any]] = None) -> str:
    """Create a human-friendly final travel plan response."""
    lines = [
        f"🗺️  {travel_intent['duration_days']}-day {travel_intent['destination']} travel plan",
        f"👥  Group: {travel_intent['group_type'].title()}",
        f"💰  Budget: ₹{travel_intent.get('budget_inr', 0):,}",
        "",
        f"🌤️  Weather: {weather.get('weather_summary', 'N/A')}",
        "",
    ]

    if vision_result:
        lines.append(f"🏨  Hotel style from image: {vision_result.get('style', 'N/A')}")
        lines.append("")

    lines.append("📅  Itinerary summary:")
    for day in itinerary.get("itinerary", [])[:3]:
        lines.append(f"- Day {day['day']}: {day['city']}")

    return "\n".join(lines)


async def run_lab() -> None:
    """Run three example orchestrator scenarios."""
    print("=== Lab 3: Orchestrator + full pipeline ===")

    print("\nTest 1: Text input")
    result1 = await orchestrator({
        "raw_text_input": "Plan a 3-day family trip to Jaipur in March.",
        "audio_path": None,
        "image_path": None,
        "processing_log": [],
    })
    print("\n".join(result1["processing_log"]))
    print("\n" + result1["final_response"])

    print("\nTest 2: Audio input")
    result2 = await orchestrator({
        "raw_text_input": None,
        "audio_path": "data/travel_query.wav",
        "image_path": None,
        "processing_log": [],
    })
    print("\n".join(result2["processing_log"]))

    print("\nTest 3: Image + text")
    result3 = await orchestrator({
        "raw_text_input": "I like heritage hotels. Plan 4 days in Udaipur.",
        "audio_path": None,
        "image_path": "data/hotel_photo.jpg",
        "processing_log": [],
    })
    print("\n".join(result3["processing_log"]))


if __name__ == "__main__":
    asyncio.run(run_lab())
