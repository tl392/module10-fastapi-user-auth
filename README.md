# FastAPI User Management

A secure user management API built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and **bcrypt** password hashing. Includes a clean HTML UI, full CRUD operations, comprehensive tests, and a GitHub Actions CI/CD pipeline that deploys to Docker Hub.

---

## Features

- **Secure User Model** — bcrypt-hashed passwords, unique constraints on `username` and `email`
- **Full CRUD** — Create, Read (single + list), Update, Delete via REST API
- **Extended Schema** — `username`, `email`, `first_name`, `last_name`, `phone_number`, `password_hash`, `created_at`
- **Pydantic Validation** — `UserCreate`, `UserUpdate`, `UserRead` schemas with field-level error messages
- **HTML UI** — Single-page interface at `/` to manage users with inline error display
- **Unit Tests** — Hashing, schema validation (no DB required)
- **Integration Tests** — Full CRUD + uniqueness + edge cases against a real PostgreSQL container
- **CI/CD** — GitHub Actions: run tests → build image → push to Docker Hub

---

## Project Structure

```
fastapi-project/
├── main.py                        # App entry point (outside app/)
├── pytest.ini                     # Pytest configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions pipeline
├── app/
│   ├── __init__.py
│   ├── database.py                # SQLAlchemy engine + session + Base
│   ├── models.py                  # User ORM model
│   ├── schemas.py                 # Pydantic schemas
│   ├── hashing.py                 # bcrypt hash + verify
│   ├── crud.py                    # CRUD operations
│   ├── routes.py                  # FastAPI router
│   └── static/
│       └── index.html             # HTML frontend
└── tests/
    ├── __init__.py
    ├── test_unit.py               # Unit tests (no DB)
    └── test_integration.py        # Integration tests (requires Postgres)
```

---

## Running Locally

### Option A — Docker Compose (recommended, zero setup)

```bash
# 1. Clone the repo
git clone https://github.com/tl392/module10-fastapi-user-auth.git
cd fastapi-project

# 2. Start Postgres + app
docker compose up --build

# 3. Open the UI
open http://localhost:8000

# 4. Browse the auto-generated API docs
open http://localhost:8000/docs
```

### Option B — Local Python (manual)

**Prerequisites:** Python 3.12+, a running PostgreSQL instance

```bash
# 1. Clone and enter the project
git clone https://github.com/tl392/module10-fastapi-user-auth.git
cd fastapi-project

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set the database connection string
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/userdb"
# Windows PowerShell:
# $env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/userdb"

# 5. (Optional) Start Postgres via Docker if you don't have one running
docker run -d \
  --name pg-local \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=userdb \
  -p 5432:5432 \
  postgres:16-alpine

# 6. Start the app (tables are auto-created on first run)
uvicorn main:app --reload

# 7. Open the UI
open http://localhost:8000
```

---

## Running Tests Locally

### Unit tests (no database needed)

```bash
# Activate your virtualenv first
source .venv/bin/activate

pytest tests/test_unit.py -v
```

### Integration tests (requires PostgreSQL)

Make sure Postgres is running and the `DATABASE_URL` is set, then:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/userdb"
pytest tests/test_integration.py -v
```

### Run all tests at once

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/userdb"
pytest -v
```

You should see output like:

```
tests/test_unit.py::TestHashing::test_hash_returns_string         PASSED
tests/test_unit.py::TestHashing::test_verify_correct_password     PASSED
...
tests/test_integration.py::TestCreateUser::test_create_success    PASSED
tests/test_integration.py::TestDeleteUser::test_delete_existing   PASSED
...
========== 35 passed in 4.21s ==========
```

---

## API Endpoints

| Method   | Path           | Description              |
|----------|----------------|--------------------------|
| `GET`    | `/`            | HTML management UI       |
| `GET`    | `/health`      | Health check             |
| `POST`   | `/users/`      | Create a user            |
| `GET`    | `/users/`      | List all users           |
| `GET`    | `/users/{id}`  | Get user by ID           |
| `PUT`    | `/users/{id}`  | Update user fields       |
| `DELETE` | `/users/{id}`  | Delete a user            |
| `GET`    | `/docs`        | Swagger UI               |

### Example — Create a user

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_doe",
    "email": "jane@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone_number": "5555555555",
    "password": "securepass"
  }'
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push to `main`:

1. **Test job** — spins up a Postgres service container, installs dependencies, runs unit tests, then integration tests.
2. **Deploy job** — builds the Docker image and pushes it to Docker Hub (only on `main` branch, after all tests pass).

### Required GitHub Secrets

| Secret                | Value                                   |
|-----------------------|-----------------------------------------|
| `DOCKERHUB_USERNAME`  | Your Docker Hub username                |
| `DOCKERHUB_TOKEN`     | Docker Hub access token (not password)  |

Go to **Settings → Secrets and variables → Actions → New repository secret** to add them.

---

## Docker Hub

Docker image: **[https://hub.docker.com/r/ltaravindh392/fastapi-user-auth](https://hub.docker.com/r/ltaravindh392/fastapi-user-auth)**

```bash
# Pull and run the latest image (requires an external Postgres)
docker pull ltaravindh392/fastapi-user-auth:latest

docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/userdb" \
  ltaravindh392/fastapi-user-auth:latest
```

---

## Reflection

### Key Experiences

Building this project reinforced how naturally FastAPI, SQLAlchemy, and Pydantic compose together. The separation of concerns — models, schemas, CRUD, routes — kept the codebase clean and made testing straightforward. Pydantic v2's `field_validator` and `model_config = {"from_attributes": True}` required small adjustments compared to v1, but the resulting schema layer is expressive and easy to reason about.

### Challenges

**Password hashing in tests** — Ensuring `password_hash` never leaks through `UserRead` required explicit checks in both the schema unit tests and the integration tests. The `model_dump()` assertion gives a clear safety net.

**Test isolation** — Integration tests share a database, so the `clean_tables` fixture (truncating between tests) was essential to prevent false failures from leftover rows.

**CI service containers** — GitHub Actions' Postgres service container needs the `pg_isready` health check; without it, tests start before the database is ready and fail intermittently.

**Pydantic email validation** — `EmailStr` requires the `pydantic[email]` extra (which pulls in `email-validator`). Forgetting this extra produces a confusing import error at runtime.
