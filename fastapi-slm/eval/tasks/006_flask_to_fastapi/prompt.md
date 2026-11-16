Migrate this Flask application to FastAPI. Keep the same URLs and behaviour, and write idiomatic FastAPI code (Pydantic models for request bodies, typed path and query parameters).

```python
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/api/greet")
def greet():
    name = request.args.get("name", "World")
    return jsonify({"greeting": f"Hello, {name}!"})


@app.route("/api/sum", methods=["POST"])
def total():
    data = request.get_json()
    numbers = data.get("numbers", [])
    return jsonify({"sum": sum(numbers)})


@app.route("/api/echo/<int:item_id>")
def echo(item_id):
    return jsonify({"id": item_id})
```

Differences you should follow in the FastAPI version: `numbers` in the `/api/sum` body is a list of numbers that defaults to an empty list, and any invalid body or a non-integer `item_id` must produce status 422 (FastAPI's default validation response).
