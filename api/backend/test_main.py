from fastapi.testclient import TestClient

from .main import api

client = TestClient(api)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {'welcome': 'to CryptoBot API'}
