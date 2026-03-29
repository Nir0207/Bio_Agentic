from fastapi.testclient import TestClient

from app.main import app


def test_validation_error_shape() -> None:
    with TestClient(app) as client:
        response = client.post('/api/v1/auth/login', json={'email': 'bad'})
        assert response.status_code == 422
        payload = response.json()
        assert 'error' in payload
        assert payload['error']['code'] == 'validation_error'
        assert 'request_id' in payload['error']


def test_auth_error_shape() -> None:
    with TestClient(app) as client:
        response = client.get('/api/v1/auth/me')
        assert response.status_code == 401
        payload = response.json()
        assert 'error' in payload
        assert payload['error']['code'] in {'http_error', 'unauthorized', 'invalid_token'}
