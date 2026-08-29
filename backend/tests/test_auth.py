from fastapi.testclient import TestClient


def test_login_rejects_bad_password(client: TestClient) -> None:
    response = client.post("/auth/login", json={"email": "hr@acme.example", "password": "nope"})
    assert response.status_code == 401


def test_me_requires_login(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_login_logout_roundtrip(auth_client: TestClient) -> None:
    me = auth_client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "hr@acme.example"
    auth_client.post("/auth/logout")
    assert auth_client.get("/auth/me").status_code == 401
