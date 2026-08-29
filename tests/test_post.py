def test_create_post_unauthenticated(client) :
    response = client.post("/auth/posts", json={"comment": "No token"})
    assert response.status_code == 401

def test_new_post(client) :
    email = "test@gmail.com"
    password = "test1234"
    
    response = client.post("/auth/register", json={"email" : email, "password" : password})
    assert response.status_code == 200
    
    response = client.post("/auth/login", json={"email" : email, "password" : password})
    assert response.status_code == 200
    tk = response.json()["token"] 
    
    headers = {"Authorization" : f"Bearer {tk}"}
    response = client.post("/auth/posts", json={"comment" : "NEW COMMENT"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["comment"] == "NEW COMMENT"
    
def test_get_user_post_successful(client) :
    email = "test@gmail.com"
    password = "test1234"
    
    response = client.post("/auth/register", json={"email" : email, "password" : password})
    assert response.status_code == 200
    id = response.json()["id"]
    
    response = client.post("/auth/login", json={"email" : email, "password" : password})
    assert response.status_code == 200
    tk = response.json()["token"] 
    
    headers = {"Authorization" : f"Bearer {tk}"}
    response = client.post("/auth/posts", json={"comment" : "NEW COMMENT"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["comment"] == "NEW COMMENT"
    
    response = client.get(f"/auth/posts/{id}", headers=headers)
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    assert len(posts) == 1
    assert posts[0]["comment"] == "NEW COMMENT"
   
    
def test_get_user_post_unsuccessful(client) :
    email = "test@gmail.com"
    password = "test1234"
    email2 = "test2@gmail.com"
    password2 = "test5678"
    
    response = client.post("/auth/register", json={"email" : email, "password" : password})
    assert response.status_code == 200
    id = response.json()["id"]
    
    response = client.post("/auth/login", json={"email" : email, "password" : password})
    assert response.status_code == 200
    tk = response.json()["token"] 
    
    response = client.post("/auth/register", json={"email" : email2, "password" : password2})
    assert response.status_code == 200
        
    response = client.post("/auth/login", json={"email" : email2, "password" : password2})
    assert response.status_code == 200
    tk2 = response.json()["token"] 
    
    headers = {"Authorization" : f"Bearer {tk2}"}
    response = client.post("/auth/posts", json={"comment" : "NEW COMMENT"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["comment"] == "NEW COMMENT"

    
    response = client.get(f"/auth/posts/{id}", headers=headers)
    assert response.status_code == 403
   
