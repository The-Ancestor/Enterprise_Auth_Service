async def test_profile_success(client):
    email = "test@gmail.com"
    password = "Pytest1234"
    response = await client.post("/auth/register", json={"email" : email, "password" : password}, headers={"x-idempotency-key": "test-key-123459"})
    assert response.status_code == 200
    login_res = await client.post("/auth/login", json={"email": email, "password": password}, headers={"User-Agent": "PytestClient/1.0"})
    assert login_res.status_code == 200
    
    token = login_res.json()["token"]
    response = await client.get("/auth/profile", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["user_agent"] == "PytestClient/1.0"
