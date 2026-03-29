import time

from fastapi.testclient import TestClient

from app.main import app


def test_login_and_me_with_default_user() -> None:
    with TestClient(app) as client:
        login_response = client.post(
            '/api/v1/auth/login',
            json={'email': 'admin@pharma.ai', 'password': 'admin123'},
        )
        assert login_response.status_code == 200
        token = login_response.json()['access_token']

        me_response = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data['email'] == 'admin@pharma.ai'


def test_register_user() -> None:
    with TestClient(app) as client:
        email = f"new-{int(time.time() * 1000)}@pharma.ai"

        register_response = client.post(
            '/api/v1/auth/register',
            json={'email': email, 'full_name': 'New User', 'password': 'strongpass'},
        )
        assert register_response.status_code == 201
        assert register_response.json()['email'] == email
