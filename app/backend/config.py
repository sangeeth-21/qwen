import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Qwen"
    app_version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8001

    google_api_key: str = ""
    google_model: str = "gemini-2.0-flash"

    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    tts_engine: str = "say"
    tts_voice: str = "Samantha"

    wake_word_enabled: bool = True
    wake_word_sensitivity: float = 0.3

    first_run: bool = True

    data_dir: str = str(Path.home() / ".qwen")

    model_config = {"env_prefix": "QWEN_", "env_file": ".env"}


settings = Settings()
