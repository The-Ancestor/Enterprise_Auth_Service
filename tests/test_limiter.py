"""async def test_too_many_requests(client) :
      response = await client.post("/auth/register", json={"email" : "test@gmail.com", "password" : "12345678"}, headers={"x-idempotency-key" : "The-One123", "X-Forwarded-For" : "127.0.0.1"})
      assert response.status_code == 200
      x = 200 
      got = False
      while x > 0 :
          response2 = await client.post("/auth/login", json={"email" : "test@gmail.com", "password" : "12345678"}, headers={"X-Forwarded-For" : "127.0.0.1"})
          if response2.status_code == 429 :
             got = True
          x = x - 1
      assert got == True
"""
