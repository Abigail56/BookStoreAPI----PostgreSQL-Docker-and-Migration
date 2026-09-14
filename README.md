# Bookstore API

FastAPI + PostgreSQL + Alembic CRUD API for authors and books, with
cookie-based session authentication guarding write endpoints.

## Architecture

![architecture](architecture.svg)

- **FastAPI app** (`app/`) — routes, ORM models, Pydantic schemas, CRUD helpers, and session auth.
- **PostgreSQL** — the only supported database backend, connected to via `DATABASE_URL` (an env var, never hardcoded).
- **SQLModel** (`app/models.py`) — declares the tables and relationships used by the API.
- **Alembic** (`alembic/`) — schema is created and evolved exclusively through migrations. `SQLModel.metadata.create_all()` is never called.
- **Docker Compose** — two services, `db` (Postgres) and `api` (this app). `entrypoint.sh` waits for the DB, runs `alembic upgrade head`, then starts `uvicorn`, so migrations run automatically on every container start.

## Data model

```
Author (1) ──< (many) Book        via Book.author_id -> Author.id (ON DELETE CASCADE)
User   (1) ──< (many) Session     server-side session store backing the auth cookie
```

The latest migration seeds 60 sample authors. Their database-generated `id`
values can be used with `GET /authors/{id}` and as `author_id` when creating
or updating books. Author writes use the authenticated `POST /authors` and
`PUT /authors/{id}` endpoints.

## Running it

1. Copy `.env.example` to `.env` (a working `.env` with dev defaults is
   already included for local use — replace the database password before
   deploying anywhere real).

2. Start everything:

   ```bash
   docker compose up --build
   ```

   This builds the API image, starts Postgres, waits for it to become
   healthy, runs the Alembic migration, and starts the API on
   `http://localhost:8000`.

3. Open the Swagger UI at **http://localhost:8000/docs**.

## Deploying on Render

Create a Render PostgreSQL database and a Docker Web Service. In the Web
Service environment variables, add `DATABASE_URL` using the database's
**Internal Database URL**. Do not use the URL in a browser and do not commit
`.env`. The container waits for PostgreSQL, runs `alembic upgrade head`, and
starts FastAPI on Render's assigned `PORT`.

## Testing via Swagger UI

1. `POST /auth/register` — create a user (`username`, `password`, min 8 chars).
2. `POST /auth/login` — logs in and sets an HttpOnly session cookie. Swagger UI's "Try it out" keeps cookies automatically, so every subsequent request in the same browser tab is authenticated.
3. `GET /auth/me` — confirms the session is active.
4. `POST /authors` — create an author (requires the session from step 2).
5. `POST /books` — create a book with that author's `id` as `author_id`.
6. `GET /authors`, `GET /authors/{id}` (includes nested books), `GET /books`, `GET /books/{id}` — all readable without auth.
7. `PUT` / `DELETE` on `/authors/{id}` and `/books/{id}` — also require the session cookie; deleting an author cascades to their books.
8. `POST /auth/logout` — clears the session; write endpoints then return `401` until you log in again.

## Local development without Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://bookstore:bookstore@localhost:5432/bookstore
alembic upgrade head
uvicorn app.main:app --reload
```

(Requires a Postgres instance reachable at that URL — `docker compose up db` is the easiest way to get one.)

## Creating a new migration

After changing `app/models.py`:

```bash
export DATABASE_URL=postgresql+psycopg://bookstore:bookstore@localhost:5432/bookstore
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Notes on the auth design

Sessions are opaque tokens stored server-side in the `sessions` table,
not self-contained JWTs — `POST /auth/logout` deletes the row, so
logout actually revokes access immediately rather than waiting for a
token to expire. The cookie is `HttpOnly` and `SameSite=Lax`. Enable
`secure=True` on the cookie once the API is served over HTTPS.
