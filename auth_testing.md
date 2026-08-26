# KhetSetu Auth Testing

1. Login with each demo account and verify the role returned by `/api/auth/login`.
2. Call `/api/auth/me` with the saved cookie and confirm session persistence.
3. Verify farmer and buyer cannot open admin metrics; admin can.
4. Verify logout clears access and `/api/auth/me` returns 401.
5. Verify invalid credentials return a friendly 401 response.