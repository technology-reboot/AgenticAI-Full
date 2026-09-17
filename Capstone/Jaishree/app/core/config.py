from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    input_dir: Path = Path("data/input")
    output_dir: Path = Path("data/output")
    ocr_language: str = "eng"
    ocr_dpi: int = 300
    min_native_text_chars: int = 40
    tesseract_cmd: str = ""
    auto_clear_max_amount: float = 1000.0
    human_review_confidence: float = 0.80
    amount_tolerance: float = 1.0
    quantity_tolerance: float = 0.01
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
