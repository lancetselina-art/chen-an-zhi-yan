import os
from pathlib import Path
from core import config
from core.knowledge import load_local_kb

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
    api_key = os.getenv("ZHIPUAI_API_KEY", "")
    return AppConfig(
        api_key=api_key,
        base_url=os.getenv("ZHIPUAI_BASE_URL", config.DEFAULT_BASE_URL),
        vision_model=os.getenv("VISION_MODEL", config.VISION_MODELS[0]),
        text_model=os.getenv("TEXT_MODEL", config.TEXT_MODELS[0]),
        demo_mode=not bool(api_key),
    )
