Create a FastAPI application protected by an API key sent in the `X-API-Key` header. The only valid key is the string `secret-key`.

- `GET /public` needs no authentication and returns `{"public": true}`.
- `GET /secure` returns `{"secure": true}` when the header is valid.
- `GET /me` returns `{"user": "admin"}` when the header is valid.

If the `X-API-Key` header is missing, protected endpoints respond with status 401. If it is present but wrong, they respond with status 403. Implement the check once as a reusable FastAPI dependency.
