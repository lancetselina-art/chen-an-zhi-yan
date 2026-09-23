import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.runtime import llm_config


client = TestClient(app)


def _settings_file(monkeypatch, tmp_path):
    path = tmp_path / 'model-settings.json'
    monkeypatch.setenv('MODEL_API_SETTINGS_FILE', str(path))
    for name in ('ZHIPUAI_API_KEY', 'ZHIPUAI_BASE_URL', 'VISION_MODEL', 'TEXT_MODEL'):
        monkeypatch.delenv(name, raising=False)
    return path


def test_model_settings_persist_and_never_return_the_api_key(monkeypatch, tmp_path):
    path = _settings_file(monkeypatch, tmp_path)
    response = client.put('/api/settings/model', json={
        'base_url': 'https://models.example/v1/',
        'api_key': 'test-secret-key',
        'vision_model': 'vision-custom',
        'text_model': 'text-custom',
    })

    assert response.status_code == 200
    data = response.json()['data']
    assert data == {
        'base_url': 'https://models.example/v1',
        'vision_model': 'vision-custom',
        'text_model': 'text-custom',
        'api_key_configured': True,
    }
    assert 'test-secret-key' not in response.text
    assert json.loads(path.read_text(encoding='utf-8'))['api_key'] == 'test-secret-key'

    saved = client.get('/api/settings/model')
    assert saved.status_code == 200
    assert saved.json()['data'] == data
    assert 'test-secret-key' not in saved.text
    assert llm_config().api_key == 'test-secret-key'
    assert llm_config().base_url == 'https://models.example/v1'
    assert llm_config().vision_model == 'vision-custom'
    assert llm_config().text_model == 'text-custom'


def test_model_connection_uses_the_saved_text_model_without_exposing_credentials(
    monkeypatch, tmp_path
):
    _settings_file(monkeypatch, tmp_path)
    client.put('/api/settings/model', json={
        'base_url': 'https://models.example/v1',
        'api_key': 'test-secret-key',
        'vision_model': 'vision-custom',
        'text_model': 'text-custom',
    })
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            calls.append({'client': kwargs})
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            calls.append({'request': kwargs})
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='OK'))])

    from core import llm
    monkeypatch.setattr(llm, 'OpenAI', FakeClient)

    response = client.post('/api/settings/model/test', json={
        'base_url': 'https://models.example/v1',
        'api_key': 'test-secret-key',
        'vision_model': 'vision-custom',
        'text_model': 'text-custom',
    })

    assert response.status_code == 200
    assert response.json()['data']['model'] == 'text-custom'
    assert 'test-secret-key' not in response.text
    assert calls[0]['client']['api_key'] == 'test-secret-key'
    assert calls[1]['request']['model'] == 'text-custom'


def test_model_connection_requires_a_configured_api_key(monkeypatch, tmp_path):
    _settings_file(monkeypatch, tmp_path)
    response = client.post('/api/settings/model/test', json={
        'base_url': 'https://models.example/v1',
        'vision_model': 'vision-custom',
        'text_model': 'text-custom',
    })

    assert response.status_code == 400
    assert 'API Key' in response.json()['error']['message']
