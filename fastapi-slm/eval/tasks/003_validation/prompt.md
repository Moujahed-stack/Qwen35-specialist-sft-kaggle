Create a FastAPI application that validates input using Pydantic v2 and FastAPI's built-in validation.

- `GET /search` has query parameters `q` (required string, at least 2 characters) and `limit` (integer, default 10, between 1 and 50 inclusive). It returns `{"q": <q>, "limit": <limit>}`.
- `POST /users` takes a JSON body with `username` (string of 3 to 20 characters, letters and digits only), `age` (integer, at least 13) and `nickname` (optional string, default null). It responds with status 201 and `{"username": ..., "age": ..., "nickname": ...}`.

Any invalid input must produce status 422.
