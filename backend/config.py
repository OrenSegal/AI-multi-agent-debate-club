import os
from pathlib import Path
import logging
from dataclasses import dataclass

@dataclass
class LLMConfig:
    api_url: str
    api_key: str
    timeout: float

@dataclass
class Config:
    base_dir: Path
    data_dir: Path
    debates_dir: Path
    log_level: str
    log_file: Path
    llm: LLMConfig

def get_config() -> Config:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    debates_dir = data_dir / "debates"
    log_file = base_dir / "logs" / "app.log"

    # Create required directories
    data_dir.mkdir(exist_ok=True)
    debates_dir.mkdir(exist_ok=True)
    log_file.parent.mkdir(exist_ok=True)

    return Config(
        base_dir=base_dir,
        data_dir=data_dir,
        debates_dir=debates_dir,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=log_file,
        llm=LLMConfig(
            api_url=os.getenv("LLM_API_URL", "https://openrouter.ai/api/v1"),
            api_key=os.getenv("LLM_API_KEY"),
            timeout=float(os.getenv("API_TIMEOUT", "60.0"))
        )
    )

def get_llm_config() -> LLMConfig:
    return get_config().llm

def setup_logging():
    config = get_config()
    logging.basicConfig(
        level=config.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.log_file)
        ]
    )
