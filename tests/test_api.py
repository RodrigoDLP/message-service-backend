import datetime, json
from unittest.mock import patch
from main.api_receiver import process_transaction
from main.schemas import RawTransaction

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_register_transaction(client):
    payload = {
        "amount": 150,
        "creditcard": 1234567890123456,
        "codigo": "ABC123",
        "email": "test@example.com",
        "datetime": datetime.datetime.now().isoformat()
    }
    response = client.post("/register-transaction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["transaction"]["amount"] == 150

def test_get_payments(client):
    response = client.get("/payments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_payments_with_data(client, mocker):
    payload = {
        "amount": 200,
        "creditcard": 9876543210987654,
        "codigo": "XYZ789",
        "email": "user@example.com",
        "datetime": datetime.datetime.now().isoformat()
    }

    def fake_publish(exchange, routing_key, body):
        data1 = json.loads(body)
        tx = RawTransaction(**data1)
        process_transaction(tx)

    mocker.patch("main.api.channel.basic_publish", side_effect=fake_publish)

    resp = client.post("/register-transaction", json=payload)
    print(resp.status_code, resp.json())

    response = client.get("/payments")
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert any(int(p["monto_final"]) == 200  for p in data)
    #and p.get("email") == "user@example.com"