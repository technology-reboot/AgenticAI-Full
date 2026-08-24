import math
import struct
import sys
import wave
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(PROJECT_ROOT))
from common import SAMPLE_MEETING_TRANSCRIPT, get_client  # noqa: E402


def create_audio_file(path: Path) -> None:
    """Create the sample meeting audio.

    Uses OpenAI TTS to synthesize real speech from the sample transcript so
    lab3's Whisper step has real audio to transcribe. Falls back to a
    synthetic tone when no API key is configured, so the lab still runs.
    """
    client = get_client()
    if client is not None:
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input=SAMPLE_MEETING_TRANSCRIPT,
            response_format="wav",
        ) as response:
            response.stream_to_file(path)
        return

    sample_rate = 16000
    duration_seconds = 3.0
    frequency = 440
    amplitude = 16000

    frames = []
    for i in range(int(sample_rate * duration_seconds)):
        sample = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
        frames.append(sample)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"".join(struct.pack("<h", s) for s in frames))


def create_chart_file(path: Path) -> None:
    """Create a simple bar chart image using matplotlib."""
    regions = ["North", "South", "East", "West"]
    q1 = [42, 38, 29, 33]
    q2 = [37, 41, 31, 35]

    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    x = range(len(regions))
    ax.bar([i - 0.2 for i in x], q1, width=0.35, label="Q1", color="#7b1fa2")
    ax.bar([i + 0.2 for i in x], q2, width=0.35, label="Q2", color="#ffb300")

    ax.set_xticks(list(x))
    ax.set_xticklabels(regions)
    ax.set_ylabel("Revenue (₹ lakhs)")
    ax.set_title("Q1 vs Q2 Revenue by Region")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    audio_path = DATA_DIR / "meeting_audio.wav"
    chart_path = DATA_DIR / "bar_chart.png"

    create_audio_file(audio_path)
    create_chart_file(chart_path)

    print(f"Created {audio_path}")
    print(f"Created {chart_path}")
