"""Shared helpers for the Azure travel planner training labs.

This module keeps the examples simple and readable for training purposes.
It supports two modes:
1. Live Azure OpenAI mode (when credentials are configured)
2. Demo mode (offline fallback so the scripts still run and teach the flow)
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


def load_environment() -> Dict[str, str]:
    """Load environment variables from .env and return them as a dictionary."""
    load_dotenv(PROJECT_ROOT / ".env")
    return {key: os.getenv(key, "") for key in [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_WHISPER_DEPLOYMENT",
        "OPENWEATHER_API_KEY",
    ]}


def get_clients() -> Tuple[AzureOpenAI, AsyncAzureOpenAI, str, str]:
    """Create Azure OpenAI clients for the lab scripts."""
    env = load_environment()
    endpoint = env["AZURE_OPENAI_ENDPOINT"].strip()
    api_key = env["AZURE_OPENAI_API_KEY"].strip()

    if not endpoint or not api_key:
        raise RuntimeError(
            "Azure credentials are missing. Please copy .env.example to .env "
            "and fill in your Azure OpenAI values."
        )

    deployment = env["AZURE_OPENAI_DEPLOYMENT"] or "gpt-4o"
    whisper_deployment = env["AZURE_OPENAI_WHISPER_DEPLOYMENT"] or "whisper"

    sync_client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-02-01",
    )
    async_client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-02-01",
    )

    return sync_client, async_client, deployment, whisper_deployment


def encode_image_b64(path: str) -> str:
    """Read an image file and convert it to a base64 string."""
    with open(path, "rb") as handle:
        return base64.b64encode(handle.read()).decode("utf-8")


def demo_travel_intent() -> Dict[str, Any]:
    """Return a simple, readable demo travel intent for offline training."""
    return {
        "destination": "Rajasthan",
        "duration_days": 5,
        "travel_month": "February",
        "group_type": "family",
        "preferences": ["heritage sites", "local food markets"],
        "accommodation_preference": "heritage hotels or havelis",
        "budget_inr": 200000,
        "special_requirements": [],
    }


def demo_vision_result() -> Dict[str, Any]:
    """Return a demo hotel analysis result for training."""
    return {
        "location_type": "heritage haveli",
        "style": "traditional Rajasthani",
        "visible_amenities": ["courtyard", "traditional architecture", "garden"],
        "quality_tier": "mid-range",
        "recommended_for": ["families", "heritage lovers"],
        "estimated_price_tier": "3000-8000/night",
    }


def demo_itinerary() -> Dict[str, Any]:
    """Create a demo itinerary that is easy to read."""
    return {
        "destination": "Rajasthan",
        "duration_days": 5,
        "itinerary": [
            {
                "day": 1,
                "city": "Jaipur",
                "morning": "Visit Amber Fort and enjoy the palace views.",
                "afternoon": "Explore the bazaars and try local snacks.",
                "evening": "Watch a folk dance show in the old city.",
                "accommodation": "Heritage haveli in the old city",
                "meals": {
                    "breakfast": "Masala chai and kachori",
                    "lunch": "Dal baati churma",
                    "dinner": "Rajasthani thali",
                },
            },
            {
                "day": 2,
                "city": "Jodhpur",
                "morning": "Discover Mehrangarh Fort.",
                "afternoon": "Walk through the blue lanes and local markets.",
                "evening": "Enjoy rooftop dining with desert views.",
                "accommodation": "Boutique haveli",
                "meals": {
                    "breakfast": "Pyaaz ki kachori",
                    "lunch": "Mutton curry and rice",
                    "dinner": "Street food tasting tour",
                },
            },
        ],
        "estimated_cost_inr": 190000,
        "travel_tips": [
            "Book heritage stays early in February.",
            "Carry light layers for cool mornings.",
        ],
    }


def demo_weather() -> Dict[str, Any]:
    """Create a demo weather response."""
    return {
        "destination": "Rajasthan",
        "month": "February",
        "weather_summary": "February is usually cool and pleasant in Rajasthan, which makes it a great month for sightseeing.",
        "avg_temp_celsius": {"min": 12, "max": 28},
        "outdoor_activity_windows": ["9:00 AM to 12:00 PM", "4:00 PM to 7:00 PM"],
        "packing_essentials": ["Light jackets", "Sunglasses", "Comfortable walking shoes"],
        "weather_risks": ["Dry air in the afternoons"],
        "indoor_alternatives": ["Museums", "Palace tours", "Cooking classes"],
    }


def pretty_print_json(data: Dict[str, Any]) -> None:
    """Print JSON in a readable indented format."""
    print(json.dumps(data, indent=2))
