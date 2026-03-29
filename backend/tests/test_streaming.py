from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient) -> str:
    response = client.post(
        '/api/v1/auth/login',
        json={'email': 'admin@pharma.ai', 'password': 'admin123'},
    )
    assert response.status_code == 200
    return response.json()['access_token']


def test_orchestration_stream_contains_expected_events() -> None:
    with TestClient(app) as client:
        token = _login(client)

        response = client.post(
            '/api/v1/orchestration/stream',
            json={'query': 'EGFR inhibitor evidence', 'high_stakes': False},
            headers={'Authorization': f'Bearer {token}'},
        )

        assert response.status_code == 200
        assert 'event: start' in response.text
        assert 'event: payload' in response.text
        assert 'event: done' in response.text
