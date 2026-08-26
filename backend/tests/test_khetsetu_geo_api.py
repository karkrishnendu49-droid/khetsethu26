"""Tests for new KhetSetu geo/map/weather/market/integrations/logistics endpoints."""
import os
import requests
import pytest

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


def login(email, password):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return s


# --- Public geo endpoints ---
def test_geo_route_public():
    r = requests.get(f"{BASE_URL}/api/geo/route", params={
        "from_lat": 23.471, "from_lon": 88.5565, "to_lat": 22.5726, "to_lon": 88.3639
    })
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("distance_km", "duration_min", "transport_cost", "geometry", "source"):
        assert k in d, f"missing {k}"
    assert d["source"] in ("osrm", "estimate")
    assert isinstance(d["geometry"], list) and len(d["geometry"]) >= 2
    assert d["distance_km"] > 0


def test_geo_geocode_public():
    r = requests.get(f"{BASE_URL}/api/geo/geocode", params={"q": "Kalyani"})
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("lat", "lon", "display_name", "source"):
        assert k in d
    assert d["source"] in ("nominatim", "gazetteer", "fallback")


def test_weather_public():
    r = requests.get(f"{BASE_URL}/api/weather", params={"lat": 23.47, "lon": 88.55})
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("temperature", "rainfall", "humidity", "condition", "forecast", "demo", "source"):
        assert k in d, f"missing {k}"
    assert isinstance(d["forecast"], list) and len(d["forecast"]) == 3


def test_market_prices_public_and_filter():
    r = requests.get(f"{BASE_URL}/api/market-prices")
    assert r.status_code == 200
    data = r.json()
    rows = data["rows"] if isinstance(data, dict) else data
    assert isinstance(rows, list) and len(rows) > 0
    row = rows[0]
    for k in ("crop", "market", "location", "price", "unit", "date", "source"):
        assert k in row
    assert row["source"] == "Demo / Prototype Data"

    r2 = requests.get(f"{BASE_URL}/api/market-prices", params={"crop": "Tomato", "location": "Kolkata"})
    assert r2.status_code == 200
    fdata = r2.json()
    filtered = fdata["rows"] if isinstance(fdata, dict) else fdata
    assert all("tomato" in x["crop"].lower() for x in filtered)
    assert all("kolkata" in x["location"].lower() for x in filtered)


# --- Auth-required endpoints ---
def test_marketplace_has_matching_fields():
    s = login("buyer@khetsetu.in", "buyer123")
    r = s.get(f"{BASE_URL}/api/marketplace")
    assert r.status_code == 200
    items = r.json()
    assert items, "expected seeded marketplace listings"
    item = items[0]
    for k in ("latitude", "longitude", "distance_km", "match_score", "match_explanation", "match_factors"):
        assert k in item, f"missing {k} in marketplace item"
    factors = item["match_factors"]
    for f in ("crop", "quantity", "price", "distance", "demand"):
        assert f in factors, f"missing match factor {f}"


def test_map_overview_auth():
    s = login("buyer@khetsetu.in", "buyer123")
    r = s.get(f"{BASE_URL}/api/map/overview")
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("listings", "buyers", "markets"):
        assert k in d
    assert len(d["markets"]) >= 4
    if d["listings"]:
        assert "match_score" in d["listings"][0]


def test_orders_logistics_auth():
    s = login("buyer@khetsetu.in", "buyer123")
    orders = s.get(f"{BASE_URL}/api/orders").json()
    assert orders
    order_id = orders[0]["order_id"]
    r = s.get(f"{BASE_URL}/api/orders/{order_id}/logistics")
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("pickup", "delivery", "route"):
        assert k in d
    for k in ("distance_km", "duration_min", "transport_cost", "geometry"):
        assert k in d["route"], f"missing route.{k}"


def test_create_order_has_logistics_fields():
    buyer = login("buyer@khetsetu.in", "buyer123")
    listings = buyer.get(f"{BASE_URL}/api/marketplace", params={"search": "Tomato"}).json()
    assert listings
    pid = listings[0]["id"]
    r = buyer.post(f"{BASE_URL}/api/orders", json={"produce_id": pid, "quantity": 1})
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("transport_cost", "distance_km", "eta_min"):
        assert k in d, f"order missing {k}"


def test_produce_geocoded_on_create():
    farmer = login("farmer@khetsetu.in", "farmer123")
    payload = {
        "crop": "GeoTestCrop", "quantity": 5, "unit": "kg", "grade": "Grade A",
        "harvest_date": "2026-04-10", "expected_price": 25,
        "location": "Kalyani", "description": "geo test",
        "village": "Kalyani", "district": "Nadia", "state": "West Bengal"
    }
    r = farmer.post(f"{BASE_URL}/api/produce", json=payload)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("latitude") is not None and d.get("longitude") is not None, f"lat/lon missing: {d}"
    farmer.delete(f"{BASE_URL}/api/produce/{d['id']}")


# --- Admin integrations ---
def test_admin_integrations_status_and_tests():
    admin = login("admin@khetsetu.in", "admin123")
    r = admin.get(f"{BASE_URL}/api/admin/integrations")
    assert r.status_code == 200, r.text
    data = r.json()
    services = data if isinstance(data, list) else data.get("services", data.get("integrations"))
    assert services and len(services) >= 4
    names = {s.get("name", s.get("service", "")).lower() for s in services}
    for expected in ("maps", "weather", "market", "geolocation"):
        assert any(expected in n for n in names), f"missing service {expected}: {names}"
    # No actual key values exposed (field name "key_configured" is a bool flag, not a key)
    import json as _json
    dumped = _json.dumps(data).lower()
    # ensure no long secret-looking strings are present
    assert "\"api_key\":" not in dumped and "\"secret\":" not in dumped

    for svc in ("maps", "weather", "market"):
        rt = admin.post(f"{BASE_URL}/api/admin/integrations/test/{svc}")
        assert rt.status_code == 200, f"{svc}: {rt.text}"
        rd = rt.json()
        assert rd.get("result") in ("success", "demo", "failed") or rd.get("status") in ("success", "demo", "failed")


def test_admin_integrations_forbidden_non_admin():
    farmer = login("farmer@khetsetu.in", "farmer123")
    r = farmer.get(f"{BASE_URL}/api/admin/integrations")
    assert r.status_code == 403
