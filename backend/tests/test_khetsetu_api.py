"""Regression coverage for KhetSetu auth, produce, marketplace, orders, and role APIs."""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


def login(email, password):
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return session, response.json()


def test_root_and_demo_logins_and_session():
    assert requests.get(f"{BASE_URL}/api/").json()["status"] == "ready"
    for email, password, role in [
        ("farmer@khetsetu.in", "farmer123", "farmer"),
        ("buyer@khetsetu.in", "buyer123", "buyer"),
        ("admin@khetsetu.in", "admin123", "admin"),
    ]:
        session, user = login(email, password)
        assert user["email"] == email and user["role"] == role
        me = session.get(f"{BASE_URL}/api/auth/me")
        assert me.status_code == 200 and me.json()["id"] == user["id"]


def test_invalid_login_and_logout():
    response = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "farmer@khetsetu.in", "password": "wrong123"})
    assert response.status_code == 401 and "incorrect" in response.json()["detail"]
    session, _ = login("farmer@khetsetu.in", "farmer123")
    assert session.post(f"{BASE_URL}/api/auth/logout").status_code == 200
    assert session.get(f"{BASE_URL}/api/auth/me").status_code == 401


def test_farmer_dashboard_produce_crud_and_search():
    session, _ = login("farmer@khetsetu.in", "farmer123")
    dashboard = session.get(f"{BASE_URL}/api/dashboard")
    assert dashboard.status_code == 200 and "stats" in dashboard.json()
    crop = f"TestCrop{uuid.uuid4().hex[:8]}"
    payload = {"crop": crop, "quantity": 12, "unit": "kg", "grade": "Grade A", "harvest_date": "2026-04-05", "expected_price": 31, "location": "Nadia", "description": "test"}
    created = session.post(f"{BASE_URL}/api/produce", json=payload)
    assert created.status_code == 200 and created.json()["crop"] == crop
    item_id = created.json()["id"]
    fetched = session.get(f"{BASE_URL}/api/produce", params={"search": crop})
    assert fetched.status_code == 200 and any(item["id"] == item_id for item in fetched.json())
    deleted = session.delete(f"{BASE_URL}/api/produce/{item_id}")
    assert deleted.status_code == 200
    assert not any(item["id"] == item_id for item in session.get(f"{BASE_URL}/api/produce").json())


def test_marketplace_order_status_notifications_and_prices():
    farmer, _ = login("farmer@khetsetu.in", "farmer123")
    buyer, _ = login("buyer@khetsetu.in", "buyer123")
    listings = buyer.get(f"{BASE_URL}/api/marketplace", params={"search": "Tomato"})
    assert listings.status_code == 200 and listings.json()
    produce_id = listings.json()[0]["id"]
    order = buyer.post(f"{BASE_URL}/api/orders", json={"produce_id": produce_id, "quantity": 1})
    assert order.status_code == 200 and order.json()["status"] == "pending"
    order_id = order.json()["order_id"]
    updated = farmer.patch(f"{BASE_URL}/api/orders/{order_id}/status", json={"status": "accepted"})
    assert updated.status_code == 200 and updated.json()["status"] == "accepted"
    assert any(o["order_id"] == order_id for o in farmer.get(f"{BASE_URL}/api/orders").json())
    notes = farmer.get(f"{BASE_URL}/api/notifications")
    assert notes.status_code == 200 and notes.json()
    assert farmer.patch(f"{BASE_URL}/api/notifications/read").status_code == 200
    prices = farmer.get(f"{BASE_URL}/api/prices")
    assert prices.status_code == 200 and {p["crop"] for p in prices.json()} >= {"Tomato", "Potato", "Onion"}


def test_admin_authorization_and_metrics():
    farmer, _ = login("farmer@khetsetu.in", "farmer123")
    assert farmer.get(f"{BASE_URL}/api/admin/metrics").status_code == 403
    admin, _ = login("admin@khetsetu.in", "admin123")
    metrics = admin.get(f"{BASE_URL}/api/admin/metrics")
    assert metrics.status_code == 200 and metrics.json()["farmers"] > 0
