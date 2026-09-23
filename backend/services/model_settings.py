import json
import os
import tempfile
from pathlib import Path
from typing import Any

from core import config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / 'data' / 'model_api_settings.local.json'


def _settings_path() -> Path:
    return Path(os.getenv('MODEL_API_SETTINGS_FILE', str(DEFAULT_SETTINGS_PATH)))


def _read_saved() -> dict[str, Any]:
    path = _settings_path()
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise RuntimeError('本机模型 API 配置文件格式错误') from exc
    return value if isinstance(value, dict) else {}


def resolved_settings() -> dict[str, str]:
    saved = _read_saved()
    return {
        'base_url': saved.get('base_url') or os.getenv('ZHIPUAI_BASE_URL') or config.DEFAULT_BASE_URL,
        'api_key': saved.get('api_key') if 'api_key' in saved else os.getenv('ZHIPUAI_API_KEY', ''),
        'vision_model': saved.get('vision_model') or os.getenv('VISION_MODEL') or config.VISION_MODELS[0],
        'text_model': saved.get('text_model') or os.getenv('TEXT_MODEL') or config.TEXT_MODELS[0],
    }


def public_settings() -> dict[str, Any]:
    values = resolved_settings()
    return {
        'base_url': values['base_url'],
        'vision_model': values['vision_model'],
        'text_model': values['text_model'],
        'api_key_configured': bool(values['api_key']),
    }


def save_settings(payload) -> dict[str, Any]:
    saved = _read_saved()
    saved.update({
        'base_url': payload.base_url,
        'vision_model': payload.vision_model,
        'text_model': payload.text_model,
    })
    if payload.clear_api_key:
        saved.pop('api_key', None)
    elif payload.api_key:
        saved['api_key'] = payload.api_key

    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=path.parent,
            prefix='.model-api-settings-', suffix='.tmp', delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            json.dump(saved, temp_file, ensure_ascii=False, indent=2)
            temp_file.write('\n')
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    return public_settings()
