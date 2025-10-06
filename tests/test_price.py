from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_price_no_discount():
    payload = {"base_price": 100.0, "vat_rate": 0.2}
    r = client.post("/v1/price", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["vat_amount"] == 20.0
    assert data["discount_amount"] == 0.0
    assert data["final_price"] == 120.0

def test_price_with_discount():
    payload = {"base_price": 100.0, "vat_rate": 0.2, "discount_code": "WELCOME10"}
    r = client.post("/v1/price", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["vat_amount"] == 20.0     # 20% of 100
    assert data["discount_amount"] == 12.0  # 10% of 120
    assert data["final_price"] == 108.0

def test_invalid_discount_code():
    payload = {"base_price": 100.0, "vat_rate": 0.2, "discount_code": "NOPE"}
    r = client.post("/v1/price", json=payload)
    assert r.status_code == 400
