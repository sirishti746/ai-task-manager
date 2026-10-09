# AI-Powered Task Management System

A REST API for managing tasks, built with **FastAPI**, **PostgreSQL**, **SQLAlchemy** and **Alembic**. Users register and log in with JWT authentication, create and manage their own tasks, and admins can see every task and change task status. An **AI endpoint** uses an LLM (Google Gemini) to generate a task description from a title.

Built for the Kanishka Software 24-hour internship assessment.

## Table of contents

1. [Tech stack](#tech-stack)
2. [Python version](#python-version)
3. [Setup instructions](#setup-instructions)
4. [Database configuration](#database-configuration)
5. [Environment variables](#environment-variables)
6. [AI configuration](#ai-configuration)
7. [How to run](#how-to-run)
8. [API endpoints](#api-endpoints)
9. [Error format and status codes](#error-format-and-status-codes)
10. [Test credentials](#test-credentials)
11. [AI feature implemented](#ai-feature-implemented)
12. [Postman collection](#postman-collection)
13. [Project structure](#project-structure)
14. [Important assumptions and decisions](#important-assumptions-and-decisions)

## Tech stack

| Area | Choice |
|---|---|
| Language | Python 3.12 |
| Web framework | FastAPI (served by Uvicorn) |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Authentication | JWT (PyJWT, HS256) |
| Password hashing | bcrypt |
| Settings | pydantic-settings (reads `.env`) |
| HTTP client for AI | httpx |
| LLM | Google Gemini (REST API) |

## Python version

**Python 3.12** (developed and tested on Windows with 3.12).

## Setup instructions

The commands below are for Windows Command Prompt (cmd). On Linux or macOS, use `source venv/bin/activate` instead of `venv\Scripts\activate` and `cp` instead of `copy`.

**1. Get the code and enter the project folder**

```cmd
git clone <repository-url>
cd ai-task-manager
```

**2. Create and activate a virtual environment**

```cmd
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```cmd
pip install -r requirements.txt
```

**4. Create the PostgreSQL database** (see [Database configuration](#database-configuration))

```cmd
psql -U postgres -c "CREATE DATABASE task_manager;"
```

**5. Create your `.env` file** from the template, then edit it (see [Environment variables](#environment-variables))

```cmd
copy .env.example .env
```

**6. Apply the database migrations**

```cmd
alembic upgrade head
```

**7. Load the sample data** (creates the test admin, test user and sample tasks)

```cmd
python -m app.database.seed
```

Then follow [How to run](#how-to-run).

## Database configuration

- **Database:** PostgreSQL (developed with version 18; any recent version works).
- **Database name:** `task_manager` (you can use another name, just match it in `DATABASE_URL`).
- **Driver:** `psycopg2-binary`.
- **Schema is created only by Alembic migrations**, never by application code. The initial migration creates the `users` and `tasks` tables.
- **Seed data** is inserted by a Python script (`app/database/seed.py`). There is no SQL file.

`DATABASE_URL` format:

```
postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>
```

If your password contains special characters (such as `@`, `/` or `%`), URL-encode them (for example `@` becomes `%40`).

Useful Alembic commands:

| Command | Meaning |
|---|---|
| `alembic upgrade head` | Apply all migrations |
| `alembic current` | Show the current revision |
| `alembic downgrade -1` | Undo the last migration |
| `alembic downgrade base` | Undo everything (empties the schema) |

`alembic.ini` does not contain a database URL. `alembic/env.py` reads `DATABASE_URL` from the same settings the app uses, so credentials never live in a committed file.

## Environment variables

Copy `.env.example` to `.env` and fill in the values. **Never commit `.env`**; it is listed in `.gitignore`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | none | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | none | Secret used to sign tokens. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Token lifetime in minutes |
| `AI_API_KEY` | For the AI feature | empty | Gemini API key. If empty, the AI endpoint returns 503 and the rest of the app works normally |
| `AI_MODEL` | No | `gemini-2.5-flash` | Gemini model name |
| `AI_BASE_URL` | No | `https://generativelanguage.googleapis.com/v1beta` | Provider base URL |
| `AI_TIMEOUT_SECONDS` | No | `15` | How long to wait for the AI provider before giving up |

The app refuses to start if a required variable is missing.

## AI configuration

The AI feature uses the **Google Gemini API**.

1. Create a key at <https://aistudio.google.com> ("Get API key"). A free tier may be available; check the current limits on that page.
2. Put the key in your `.env` file:

   ```
   AI_API_KEY=your-key-here
   AI_MODEL=gemini-2.5-flash
   ```

   Model names change over time. If the model is retired, copy the current model name from Google AI Studio into `AI_MODEL`.
3. Restart the server after editing `.env`.

Security notes:

- The key is read only through `app/config.py` from the environment. It is never hardcoded, never logged and never returned in any response.
- It is sent to the provider in a request header, not in the URL.
- `.env.example` contains only a placeholder.

Without a key, `POST /api/tasks/generate-description` returns **503** `AI service is not configured`; everything else keeps working.

## How to run

```cmd
uvicorn app.main:app --reload --reload-dir app
```

| URL | What it is |
|---|---|
| <http://127.0.0.1:8000/docs> | **Interactive Swagger UI. Start here.** |
| <http://127.0.0.1:8000/health> | Health check, returns `{"status": "ok"}` |

The root URL `/` has no page and returns 404 by design; use `/docs`.

**Using Swagger with authentication:** call `POST /api/auth/login`, copy the `access_token` value, click the green **Authorize** button and paste **only the token** (Swagger adds the `Bearer` prefix). Refreshing the page clears the token.

## API endpoints

| Method | URL | Who can call | Success | Possible errors |
|---|---|---|---|---|
| POST | `/api/auth/register` | Anyone | 201 | 409 email exists, 422 |
| POST | `/api/auth/login` | Anyone | 200 | 401 wrong credentials, 422 |
| POST | `/api/tasks` | Any logged-in user | 201 | 401, 422 |
| GET | `/api/tasks` | Any logged-in user (user: own tasks, admin: all tasks) | 200 | 401 |
| POST | `/api/tasks/generate-description` | Any logged-in user | 200 | 401, 422, 502 AI failure, 503 AI not configured |
| GET | `/api/tasks/{task_id}` | Task owner or admin | 200 | 401, 403, 404, 422 |
| PUT | `/api/tasks/{task_id}` | Task owner or admin (title and description only) | 200 | 401, 403, 404, 422 |
| PATCH | `/api/tasks/{task_id}/status` | **Admin only** | 200 | 401, 403, 404, 422 |
| GET | `/health` | Anyone | 200 | none |

Request bodies:

| Endpoint | Body |
|---|---|
| Register | `{"name": "...", "email": "...", "password": "..."}` (password 8 to 72 characters) |
| Login | `{"email": "...", "password": "..."}` returns `{"access_token": "...", "token_type": "bearer"}` |
| Create task | `{"title": "...", "description": "..."}` (description optional) |
| Update task | `{"title": "...", "description": "..."}` (both optional) |
| Update status | `{"status": "Pending" \| "In Progress" \| "Testing" \| "Completed"}` |
| Generate description | `{"title": "..."}` returns `{"description": "..."}` |

Send the token on every protected request as `Authorization: Bearer <token>`.

**Who may do what**

| Action | Regular user | Admin |
|---|---|---|
| Create task | Yes | Yes |
| View tasks | Own tasks only | All tasks |
| Edit task (title, description) | Own tasks only | Any task |
| Update task status | No (403) | Yes |
| Use the AI endpoint | Yes | Yes |

## Error format and status codes

Every error response is JSON with a `detail` message:

```json
{"detail": "Task not found"}
```

Validation errors (422) also list each failing field. The submitted values are never echoed back, so a rejected password cannot leak into a response or a log:

```json
{
  "detail": "Validation failed",
  "errors": [{"field": "email", "message": "value is not a valid email address"}]
}
```

| Code | Meaning | When it happens |
|---|---|---|
| 200 | OK | Login, read, update, AI description |
| 201 | Created | Register, create task |
| 401 | Unauthorized | Wrong email or password; missing, invalid or expired JWT |
| 403 | Forbidden | Regular user changing status; accessing another user's task |
| 404 | Not Found | Task id does not exist |
| 409 | Conflict | Email already registered |
| 422 | Unprocessable Entity | Invalid request data |
| 500 | Internal Server Error | Database error or unexpected bug (generic message only) |
| 502 | Bad Gateway | AI provider timeout, network error, provider error, or unusable response |
| 503 | Service Unavailable | AI feature not configured (no API key) |

FastAPI also returns 405 automatically when the wrong HTTP method is used on a URL.

## Test credentials

> **LOCAL TESTING ONLY.** These accounts are created by the seed script. Never use these credentials on a real or deployed system.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin@12345` |
| Regular user | `user@example.com` | `User@12345` |

Create them with `python -m app.database.seed`. The script is idempotent: running it again skips anything that already exists. It also creates a few sample tasks in different statuses.

## AI feature implemented

**`POST /api/tasks/generate-description`** takes a task title and returns a short description generated by the Gemini LLM.

```json
// Request
{"title": "Fix login bug"}

// Response 200
{"description": "Investigate why users cannot sign in ..."}
```

How it works:

- All LLM code lives in `app/ai/`. `client.py` is the only file that talks to the provider, and it knows nothing about users, tasks or the database.
- The prompt asks for 2 to 4 plain-text sentences. The instructions are sent as a system instruction, and the title is passed as clearly delimited data.
- The title must be 1 to 200 characters.

Validation and failure handling:

| Situation | Result |
|---|---|
| No API key configured | 503 `AI service is not configured` |
| Provider timeout or network error | 502 `AI service failed. Please try again later.` |
| Provider returns an HTTP error (bad key, quota, outage) | 502 (same generic message) |
| Response has an unexpected shape, is empty, is not text, or is longer than 2000 characters | 502 (same generic message) |

The client never sees the API key or the provider's raw error text. Details are written to the server log (status codes only, never the key).

## Postman collection

`postman/task_manager.postman_collection.json` contains 29 requests in five folders: **Auth**, **User Tasks**, **Admin Tasks**, **Authorization Failures** and **AI**. Each request has test scripts that assert status codes.

1. Make sure the server is running and the seed script has been run.
2. In Postman choose **Import** and select the JSON file.
3. Open the collection and click **Run** (Collection Runner). Keep the folder order.

Collection variables: `base_url`, `user_token`, `admin_token`, `task_id` (plus helpers `admin_task_id`, `user_id`, `new_email`). The login requests save the tokens automatically.

The AI request needs a valid `AI_API_KEY` to return 200. Without one it returns 503, and the test still passes because it accepts 200, 502 and 503.

## Project structure

```
ai-task-manager/
  app/
    main.py              FastAPI app, routers, global error handlers, /health
    config.py            the only place that reads .env
    api/                 HTTP layer: auth.py, tasks.py (thin, call services)
    auth/                security.py (hashing, JWT), dependencies.py (get_current_user, require_admin)
    models/              SQLAlchemy models: user.py, task.py
    schemas/             Pydantic request/response schemas: user.py, task.py, ai.py
    services/            business logic and ownership checks: user_service.py, task_service.py
    ai/                  client.py (the only LLM code), exceptions.py
    database/            base.py, session.py, seed.py
  alembic/               migration environment and versions/
  alembic.ini
  postman/               Postman collection
  .env.example
  requirements.txt
  README.md
```

Layering rule: `api` calls `services`, and `services` use `models`. The API layer never touches the database directly, services know nothing about HTTP, and the AI module knows nothing about users, tasks or the database.

## Important assumptions and decisions

**Authentication and users**

- **The password column is named `password_hash`.** Plain passwords are never stored. They are hashed with bcrypt, which adds a random salt and is deliberately slow.
- **bcrypt is used directly** (not passlib, which has compatibility problems with current bcrypt). bcrypt only reads the first 72 bytes, so passwords are limited to 8 to 72 characters.
- **Registration always creates a regular user.** The register schema has no role field, so nobody can make themselves an admin. Admin accounts are created only by the seed script.
- **The role is never trusted from the JWT.** The token holds only the user id, expiry and issue time. On every request the user and their current role are re-read from the database, so a role change or a deleted user takes effect immediately.
- **Tokens last 30 minutes** with no refresh and no revocation. This keeps the system simple, and the short lifetime limits the damage of a stolen token.
- **Wrong email and wrong password return the same 401 message**, and a dummy hash check keeps response times similar, so the login endpoint does not reveal which emails are registered.
- Emails are stored in lowercase, so `A@x.com` and `a@x.com` are the same account.

**Tasks and authorization**

- **A task's owner comes from the JWT**, never from the request body. New tasks always start as `Pending`.
- **Regular users cannot change status, even on their own tasks**, as the assignment specifies. The status route is admin-only, enforced by a dependency before the route body runs.
- **Another user's task returns 403.** The assignment asks for this. Many production APIs return 404 instead so attackers cannot tell whether a task id exists; that would be a one-line change.
- **The task list is filtered in the database query** (`WHERE user_id = ...`) for regular users, so other users' rows are never loaded.
- **Role and status are plain string columns** validated in Python through enums, instead of native PostgreSQL ENUM types, which are awkward to change in migrations.
- Ownership rules live in `task_service.py`, and role gating lives in `auth/dependencies.py`.

**Errors and AI**

- **Database errors return a generic 500.** The session is rolled back and full details go only to the server log, never to the client.
- **The 422 handler never echoes the submitted input**, so passwords cannot appear in error responses.
- **AI failures are mapped centrally:** a missing key becomes 503, and every provider or response problem becomes 502 with a generic message.
- **The AI output is only a suggestion** returned to the caller. It is never executed, and it is length-capped and validated as plain text.

**Other**

- Routes are plain `def` functions rather than `async def`, because SQLAlchemy with psycopg2 and httpx's synchronous calls are blocking. FastAPI runs them in a thread pool.
- The seeded credentials are public test values for local use only.
