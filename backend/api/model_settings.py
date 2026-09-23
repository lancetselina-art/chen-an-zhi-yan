from fastapi import APIRouter, HTTPException

from backend.schemas.model_settings import ModelSettingsInput
from backend.services import model_settings
from backend.services.runtime import llm_config
from core.llm import AppConfig, LLMError, test_connection


router = APIRouter()


@router.get('/api/settings/model')
def get_model_settings():
    return model_settings.public_settings()


@router.put('/api/settings/model')
def put_model_settings(payload: ModelSettingsInput):
    return model_settings.save_settings(payload)


@router.post('/api/settings/model/test')
def test_model_settings(payload: ModelSettingsInput):
    current = llm_config()
    api_key = (
        '' if payload.clear_api_key else
        payload.api_key or current.api_key
    )
    candidate = AppConfig(
        api_key=api_key,
        base_url=payload.base_url,
        vision_model=payload.vision_model,
        text_model=payload.text_model,
        temperature=current.temperature,
        timeout=20,
        demo_mode=not bool(api_key),
    )
    try:
        model = test_connection(candidate)
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'connected': True, 'model': model}
