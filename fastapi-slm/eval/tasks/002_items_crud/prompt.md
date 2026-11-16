Build an in-memory CRUD API for items using FastAPI and Pydantic v2.

An item has `name` (non-empty string) and `price` (float, strictly greater than 0).

Endpoints:

- `POST /items` takes `{"name": ..., "price": ...}`, responds with status 201 and `{"id": <int>, "name": ..., "price": ...}`. Ids start at 1 and increase by 1 for each new item.
- `GET /items` returns a list of all items in creation order.
- `GET /items/{item_id}` returns the item, or status 404 if it does not exist.
- `DELETE /items/{item_id}` responds with status 204 and no body, or 404 if the item does not exist.

Invalid request bodies must produce status 422.
