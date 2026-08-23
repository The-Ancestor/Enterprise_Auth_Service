def test_user_registration(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "underdog@example.com", 
            "password": "StrongPassword123!"
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "underdog@example.com"
    
    
def test_duplicate_email(client):
    response = client.post("/auth/register", json={"email": "un@gmail.com", "password": "1234"})
    assert response.status_code == 200
    response = client.post("/auth/register", json={"email": "un@gmail.com", "password": "1234"})
    assert response.status_code == 409
    
def test_invalid_login(client):
    response = client.post("/auth/register", json={"email": "under@gmail.com", "password": "1234"})
    assert response.status_code == 200
    response = client.post("/auth/login", json={"email": "undern@gmail.com", "password": "12345678"})
    assert response.status_code == 401
    response = client.post("/auth/login", json={"email": "asw@gmail.com", "password": "1234"})
    assert response.status_code == 401
    
def test_successful_login(client) :
    response = client.post("/auth/register", json={"email": "ace@gmail.com", "password" : "ace"})
    assert response.status_code == 200
    response = client.post("/auth/login", json={"email": "ace@gmail.com", "password" : "ace"})
    assert response.status_code == 200
    assert response.json()["token"] != None
    assert response.json()["refresh_token"] != None
    
def test_refresh_token_revocation(client):
    response = client.post("/auth/register", json={"email": "jokey@gmail.com" , "password" : "jokey"})
    assert response.status_code == 200
    response = client.post("/auth/login", json={"email": "jokey@gmail.com" , "password" : "jokey"})
    assert response.status_code == 200
    tk = response.json()["refresh_token"]
    response = client.post("/auth/refresh", json={"refresh_token" : tk})
    new_tk = response.json()["refresh_token"]
    assert new_tk != tk
    response = client.post("/auth/refresh", json={"refresh_token": tk})
    assert response.status_code == 401
    
def test_logout_revocation(client):
    response = client.post("/auth/register", json={"email": "logout_user@gmail.com", "password": "password123"})
    assert response.status_code == 200
    response = client.post("/auth/login", json={"email": "logout_user@gmail.com", "password": "password123"})
    assert response.status_code == 200
    tk = response.json()["refresh_token"]

    response = client.post("/auth/logout", json={"refresh_token": tk})
    assert response.status_code == 200

    response = client.post("/auth/refresh", json={"refresh_token": tk})
    assert response.status_code == 401
