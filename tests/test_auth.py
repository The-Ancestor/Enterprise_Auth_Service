async def test_user_registration(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "underdog@example.com", 
            "password": "StrongPassword123!"
        }, headers={"x-idempotency-key": "test-key-12345"})
    assert response.status_code == 200
    assert response.json()["email"] == "underdog@example.com"

    
async def test_duplicate_email(client):
    email = "test@gmail.com"
    password = "MAIN1234"
    response = await client.post("/auth/register", json={"email": email, "password": password}, headers={"x-idempotency-key": "test-key-123451"})
    assert response.status_code == 200
    response = await client.post("/auth/register", json={"email": email, "password": password}, headers={"x-idempotency-key": "test-key-123451"})
    assert response.json()["message"] == "success"
    assert response.status_code == 200
    
async def test_invalid_login(client):
    response = await client.post("/auth/register", json={"email": "first@gmail.com", "password": "FirstSon"}, headers={"x-idempotency-key": "test-key-123452"})
    assert response.status_code == 200
    response = await client.post("/auth/login", json={"email": "first@gmail.com", "password": "12345678"})
    assert response.status_code == 401
    response = await client.post("/auth/login", json={"email": "second@gmail.com", "password": "STRONG1234"})
    assert response.status_code == 401
    
async def test_successful_login(client) :
    email = "ace@gmail.com"
    password = "AstarMStar"
    response = await client.post("/auth/register", json={"email": email, "password" : password}, headers={"x-idempotency-key": "test-key-123453"})
    assert response.status_code == 200
    response = await client.post("/auth/login", json={"email": email, "password" : password})
    assert response.status_code == 200
    assert response.json()["token"] != None
    assert response.json()["refresh_token"] != None
    
async def test_refresh_token_revocation(client):
    email = "jokey@gmail.com"
    password = "jokey123"
    response = await client.post("/auth/register", json={"email": email, "password" : password}, headers={"x-idempotency-key": "test-key-123454"})
    assert response.status_code == 200
    response = await client.post("/auth/login", json={"email": email, "password" : password})
    assert response.status_code == 200
    tk = response.json()["refresh_token"]
    response = await client.post("/auth/refresh", json={"refresh_token" : tk})
    new_tk = response.json()["refresh_token"]
    assert new_tk != tk
    response = await client.post("/auth/refresh", json={"refresh_token": tk})
    assert response.status_code == 401
    
async def test_logout_revocation(client):
    email = "user@gmail.com"
    password = "USER123456"
    response = await client.post("/auth/register", json={"email": email, "password": password}, headers={"x-idempotency-key": "test-key-123455"})
    assert response.status_code == 200
    response = await client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    tk = response.json()["refresh_token"]

    response = await client.post("/auth/logout", json={"refresh_token": tk})
    assert response.status_code == 200

    response = await client.post("/auth/refresh", json={"refresh_token": tk})
    assert response.status_code == 401
