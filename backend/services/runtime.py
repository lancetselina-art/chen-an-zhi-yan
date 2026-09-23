import os
from pathlib import Path
from core import config
from core.knowledge import load_local_kb
from backend.services.model_settings import resolved_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

def settings():
    return {"stages": config.STAGES, "work_types": list(config.WORK_TYPES), "cities": list(config.CITY_COORDS),
            "vision_models": config.VISION_MODELS, "text_models": config.TEXT_MODELS,
            "knowledge_files": len(knowledge())}
def knowledge():
    return load_local_kb(str(KNOWLEDGE_DIR))
def llm_config():
    from core.llm import AppConfig
    values = resolved_settings()
    return AppConfig(
        api_key=values['api_key'],
        base_url=values['base_url'],
        vision_model=values['vision_model'],
        text_model=values['text_model'],
        demo_mode=not bool(values['api_key']),
    )
