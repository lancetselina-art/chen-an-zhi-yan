from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_response_shape():
    response = client.get('/api/health')
    assert response.status_code == 200
    body = response.json()
    assert body['ok'] is True
    assert body['data']['service'] == 'chen-an-zhi-yan'
    assert body['error'] is None
    assert body['request_id']


def test_config_excludes_secrets():
    response = client.get('/api/config')
    assert response.status_code == 200
    data = response.json()['data']
    assert data['stages']
    assert data['work_types']
    assert data['cities']
    assert data['vision_models']
    assert 'api_key' not in data


def test_invalid_sensor_input_has_unified_error_shape():
    response = client.post('/api/sensors/features', json={'rows': []})
    assert response.status_code == 400
    body = response.json()
    assert body['ok'] is False
    assert body['data'] is None
    assert body['error']['message']
    assert body['request_id']


def test_knowledge_search_returns_ranked_snippets():
    response = client.get('/api/knowledge/search', params={'q': '扬尘'})
    assert response.status_code == 200
    body = response.json()
    assert body['ok'] is True
    assert isinstance(body['data'], list)
    if body['data']:
        assert {'file', 'score', 'snippet'} <= body['data'][0].keys()


def test_unknown_knowledge_file_is_safe_error():
    response = client.get('/api/knowledge/../../secret.md')
    assert response.status_code in (400, 404)
    body = response.json()
    assert body['ok'] is False
    assert 'Traceback' not in str(body)


def test_demo_vision_uses_default_assets_without_upload():
    response = client.post('/api/vision/analyze', data={'demo_mode': 'true'})
    assert response.status_code == 200
    data = response.json()['data']
    assert data['input_image_url'] == '/api/vision/demo/input'
    assert data['overlay_image_url'] == '/api/vision/demo/overlay'
    assert len(data['findings']) == 6
    assert all(item['visual_evidence'] for item in data['findings'])
    assert all(item['accident_chain'] for item in data['findings'])
    assert all(item['rectification']['action'] for item in data['findings'])
    assert client.get(data['input_image_url']).status_code == 200
    assert client.get(data['overlay_image_url']).status_code == 200


def test_non_demo_vision_still_requires_upload():
    response = client.post('/api/vision/analyze', data={'demo_mode': 'false'})
    assert response.status_code == 400
    body = response.json()
    assert body['ok'] is False
    assert '上传现场图片' in body['error']['message']
