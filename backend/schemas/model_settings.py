from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator


class ModelSettingsInput(BaseModel):
    base_url: str = Field(min_length=8, max_length=500)
    api_key: str | None = Field(default=None, max_length=4096)
    vision_model: str = Field(min_length=1, max_length=200)
    text_model: str = Field(min_length=1, max_length=200)
    clear_api_key: bool = False

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        value = value.strip().rstrip('/')
        parsed = urlsplit(value)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise ValueError('Base URL 必须是有效的 http 或 https 地址')
        return value

    @field_validator('vision_model', 'text_model')
    @classmethod
    def trim_model_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('模型名称不能为空')
        return value

    @model_validator(mode='after')
    def validate_key_action(self):
        if self.clear_api_key and self.api_key:
            raise ValueError('清除密钥时不能同时提交新的 API Key')
        return self
