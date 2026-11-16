Build a todo API with FastAPI and SQLModel, stored in a SQLite database file named `todos.db` in the current working directory.

The `Todo` table has `id` (integer primary key, auto-generated), `title` (required string) and `done` (boolean, default false). Create the tables when the application starts.

Endpoints:

- `POST /todos` takes `{"title": ..., "done": ...}` (`done` optional, default false), responds with status 201 and the full todo including its `id`.
- `GET /todos` returns all todos. An optional query parameter `done` (true or false) filters by completion.
- `GET /todos/{todo_id}` returns the todo, or status 404 if it does not exist.
- `PATCH /todos/{todo_id}` takes `{"done": <bool>}`, updates only that field, and returns the updated todo, or 404 if it does not exist.
- `DELETE /todos/{todo_id}` responds with status 204, or 404 if it does not exist.

A missing or empty `title` must produce status 422.
