"""Lab 1: Speech Agent + Vision Agent.

This script demonstrates the first half of the training flow:
1. Transcribe a voice query with Whisper
2. Extract travel intent from the text
3. Analyse a hotel image with GPT-4o vision
4. Combine the outputs into an orchestrator-ready context

The code is intentionally simple and commented for training use.
"""

import json
from pathlib import Path
from typing import Any, Dict

from common import (
    DATA_DIR,
    demo_travel_intent,
    demo_vision_result,
    encode_image_b64,
    get_clients,
    pretty_print_json,
)


AUDIO_PATH = DATA_DIR / "travel_query.wav"
IMAGE_PATH = DATA_DIR / "hotel_photo.jpg"


def transcribe_audio(client, whisper_model: str) -> str:
    """Transcribe an audio file with Whisper."""
    if not AUDIO_PATH.exists():
        print("Audio file not found. Please place travel_query.wav in the data folder.")
        return "I want to plan a five-day trip to Rajasthan in February with my family."

    with open(AUDIO_PATH, "rb") as handle:
        response = client.audio.transcriptions.create(
            model=whisper_model,
            file=handle,
            language="en",
            response_format="text",
        )
    return response


def extract_travel_intent(client, deployment: str, transcript: str) -> Dict[str, Any]:
    """Ask GPT-4o to turn the transcript into structured JSON."""
    prompt = f"""Extract structured travel intent from this transcript.

Transcript: "{transcript}"

Return JSON with: destination, duration_days, travel_month, group_type,
preferences, accommodation_preference, budget_inr, special_requirements.
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def analyse_hotel_image(client, deployment: str) -> Dict[str, Any]:
    """Analyse the hotel image and return a structured JSON object."""
    if not IMAGE_PATH.exists():
        print("Image file not found. Please place hotel_photo.jpg in the data folder.")
        return {
            "location_type": "heritage haveli",
            "style": "traditional Rajasthani",
            "visible_amenities": ["courtyard", "garden"],
            "quality_tier": "mid-range",
            "recommended_for": ["families"],
            "estimated_price_tier": "3000-8000/night",
        }

    image_b64 = encode_image_b64(str(IMAGE_PATH))
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyse this hotel image. Return JSON with location_type, style, visible_amenities, quality_tier, recommended_for, estimated_price_tier.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        temperature=0.0,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def run_lab() -> None:
    """Run the full lab flow."""
    print("=== Lab 1: Speech Agent + Vision Agent ===")
    print("This example shows how speech and image input can be converted into structured JSON.")

    try:
        client, _, deployment, whisper_model = get_clients()
        print("Azure OpenAI client ready.")
    except RuntimeError as exc:
        print(f"Using demo mode: {exc}")
        client = None
        deployment = "gpt-4o"
        whisper_model = "whisper"

    # 1) Speech agent: transcribe the audio query
    if client is not None:
        transcript = transcribe_audio(client, whisper_model)
    else:
        transcript = "I want to plan a five-day trip to Rajasthan in February with my family."
        print("Demo transcription used.")

    print("\nTranscript:")
    print(transcript)

    # 2) Extract travel intent
    if client is not None:
        travel_intent = extract_travel_intent(client, deployment, transcript)
    else:
        travel_intent = demo_travel_intent()
        print("Demo travel intent used.")

    print("\nTravel intent:")
    pretty_print_json(travel_intent)

    # 3) Vision agent: analyse the hotel photo
    if client is not None:
        vision_result = analyse_hotel_image(client, deployment)
    else:
        vision_result = demo_vision_result()
        print("Demo vision result used.")

    print("\nHotel vision result:")
    pretty_print_json(vision_result)

    # 4) Merge both outputs into orchestrator-ready context
    enriched_context = {
        "travel_intent": travel_intent,
        "preferred_hotel_style": {
            "detected_from_image": True,
            "location_type": vision_result.get("location_type", "unknown"),
            "style": vision_result.get("style", "unknown"),
            "quality_tier": vision_result.get("quality_tier", "unknown"),
        },
        "orchestrator_ready": True,
    }

    print("\nMerged context for the orchestrator:")
    pretty_print_json(enriched_context)


if __name__ == "__main__":
    run_lab()
