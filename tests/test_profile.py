def test_profile_success(client):
    response = client.post("/auth/register", json={"email" :  "aws@gmail.com", "password" : "12345678"})
    assert response.status_code == 200
    login_res = client.post("/auth/login", json={"email": "aws@gmail.com", "password": "12345678"}, headers={"User-Agent": "PytestClient/1.0"})
    
    token = login_res.json()["token"]
    response = client.get("/auth/profile", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "aws@gmail.com"
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["user_agent"] == "PytestClient/1.0"
