"""CORS regression tests for KhetSetu backend.

Verifies that:
- Backend responds 200 on GET /api/ (no more 500 crashes from broken middleware)
- OPTIONS preflight succeeds for approved origins with proper CORS headers
- Disallowed origins do NOT receive CORS headers
- Actual credentialed requests carry the echoed Origin (never '*') with credentials
"""
import os
import requests
import pytest

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
# Emergent's Cloudflare ingress rewrites CORS headers for the external URL
# (returns wildcard origin regardless of backend response). To validate the
# actual FastAPI CORS middleware wiring (the piece the user asked us to fix),
# we hit the backend directly on localhost:8001. External-URL functional
# behavior is validated by test_khetsetu_api.py.
BASE_URL = "http://localhost:8001"

APPROVED_ORIGINS = [
    "https://farm-fair-connect.preview.emergentagent.com",
    "https://khetsetu.in",
    "https://www.khetsetu.in",
    "http://localhost:3000",
    "https://random-app.preview.emergentagent.com",  # regex match
]

DISALLOWED_ORIGINS = [
    "https://evil.example.com",
    "http://attacker.local",
]


def test_root_no_crash():
    r = requests.get(f"{BASE_URL}/api/")
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "ready"


@pytest.mark.parametrize("origin", APPROVED_ORIGINS)
def test_preflight_approved_origin(origin):
    r = requests.options(
        f"{BASE_URL}/api/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code in (200, 204), f"{origin} -> {r.status_code} {r.text}"
    aco = r.headers.get("access-control-allow-origin")
    assert aco == origin, f"Expected echoed origin {origin}, got {aco}"
    assert r.headers.get("access-control-allow-credentials", "").lower() == "true"
    methods = r.headers.get("access-control-allow-methods", "")
    for m in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
        assert m in methods, f"Method {m} missing from {methods}"


@pytest.mark.parametrize("origin", DISALLOWED_ORIGINS)
def test_preflight_disallowed_origin(origin):
    r = requests.options(
        f"{BASE_URL}/api/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    aco = r.headers.get("access-control-allow-origin")
    # Must NOT echo disallowed origin and must NOT be wildcard on credentialed setup
    assert aco != origin, f"Disallowed origin {origin} was echoed"
    assert aco != "*", "Wildcard on credentialed CORS is insecure"


def test_actual_login_has_cors_headers_and_cookie():
    origin = "https://farm-fair-connect.preview.emergentagent.com"
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "farmer@khetsetu.in", "password": "farmer123"},
        headers={"Origin": origin},
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("access-control-allow-origin") == origin
    assert r.headers.get("access-control-allow-credentials", "").lower() == "true"
    # HttpOnly cookie present
    set_cookie = r.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()


def test_actual_login_khetsetu_origin():
    origin = "https://khetsetu.in"
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "buyer@khetsetu.in", "password": "buyer123"},
        headers={"Origin": origin},
    )
    assert r.status_code == 200, r.text
    assert r.headers.get("access-control-allow-origin") == origin


def test_allowed_headers_present():
    r = requests.options(
        f"{BASE_URL}/api/auth/login",
        headers={
            "Origin": "https://khetsetu.in",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization,accept,origin",
        },
    )
    assert r.status_code in (200, 204)
    allowed = r.headers.get("access-control-allow-headers", "").lower()
    for h in ["content-type", "authorization", "accept", "origin"]:
        assert h in allowed, f"Header {h} missing from allow-headers: {allowed}"
