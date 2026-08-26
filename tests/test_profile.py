def test_profile_success(client):
    email = "test@gmail.com"
    password = "Pytest"
    response = client.post("/auth/register", json={"email" : email, "password" : password})
    assert response.status_code == 200
    login_res = client.post("/auth/login", json={"email": email, "password": password}, headers={"User-Agent": "PytestClient/1.0"})
    assert response.status_code == 200
    
    token = login_res.json()["token"]
    response = client.get("/auth/profile", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["user_agent"] == "PytestClient/1.0"
