def register_and_login(client):
    client.post("/api/auth/register", json={"name":"Test User","email":"test@example.com","password":"password123"})
    response = client.post("/api/auth/login", json={"email":"test@example.com","password":"password123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

def test_health(client):
    assert client.get("/api/health").json()["status"] == "healthy"

def test_auth_and_transaction_crud(client):
    headers = register_and_login(client)
    categories = client.get("/api/categories", headers=headers).json()
    food = next(c for c in categories if c["name"] == "Food")
    payload = {"kind":"expense","amount":125.5,"description":"Lunch","transaction_date":"2026-01-10","category_id":food["id"],"recurring":False}
    created = client.post("/api/transactions", json=payload, headers=headers)
    assert created.status_code == 201
    tx_id = created.json()["id"]
    assert client.get("/api/transactions", headers=headers).json()[0]["description"] == "Lunch"
    payload["amount"] = 150
    assert client.put(f"/api/transactions/{tx_id}", json=payload, headers=headers).json()["amount"] == 150
    assert client.delete(f"/api/transactions/{tx_id}", headers=headers).status_code == 204

def test_user_data_isolation(client):
    headers = register_and_login(client)
    client.post("/api/auth/register", json={"name":"Other User","email":"other@example.com","password":"password123"})
    other = client.post("/api/auth/login", json={"email":"other@example.com","password":"password123"}).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get("/api/transactions", headers=headers).json() == []
    assert client.get("/api/transactions", headers=other_headers).json() == []
