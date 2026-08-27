# Auth Testing Playbook (KhetSetu)

## API testing (cookie-based)
```
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl -c /tmp/cj.txt -X POST "$API/api/auth/login" -H "Content-Type: application/json" -d '{"email":"farmer@khetsetu.in","password":"farmer123"}'
curl -b /tmp/cj.txt "$API/api/auth/me"
```

## Forgot/reset password (demo prototype flow — no email)
1. POST /api/auth/forgot-password {"email": "..."} → returns `reset_token` in response (clearly labelled prototype behaviour).
2. POST /api/auth/reset-password {"token": "...", "new_password": "..."} → 200, then login with new password.
3. Reused/expired token → 400 with clear message.

## Role rules
- Only farmers can POST/PUT/DELETE /api/produce (buyer gets 403).
- Only buyers can POST /api/orders (farmer gets 403); quantity above availability → 400.
- Order transitions: placed→accepted/rejected (farmer only), accepted→preparing→out_for_delivery→delivered (farmer). Invalid transition → 400. Buyer cannot change status.
- Rejected orders restore produce quantity.
