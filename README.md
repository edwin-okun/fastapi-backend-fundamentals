# FastAPI Backend Fundamentals

Minimal FastAPI backend with:
- Health endpoint
- In-memory users API
- Transient failure simulation on user creation
- Async client script with retry and exponential backoff plus jitter

## Quickstart

Run these in separate terminals:

```bash
uv sync && uv run fastapi dev
uv run scripts/users.py
```

Then open:
- http://127.0.0.1:8000/docs

## Project Structure

```text
.
├── LICENSE
├── pyproject.toml
├── README.md
├── app
│   ├── __init__.py
│   ├── main.py
│   └── v1
│       ├── __init__.py
│       └── api
│           ├── __init__.py
│           ├── health.py
│           └── users.py
├── scripts
│   ├── __init__.py
│   ├── retry.py
│   └── users.py
└── tests
	├── __init__.py
	└── test_retry.py
```

## Requirements

- Python 3.14+
- uv (recommended) or pip

## Install

```bash
uv sync
```

## Run API

```bash
uv run fastapi dev
```

Server runs at:
- http://127.0.0.1:8000

Open API docs:
- http://127.0.0.1:8000/docs

## API Base Path

The app is configured with:
- root_path = /api/v1

Effective endpoint URLs:
- GET /api/v1/health/
- GET /api/v1/users/all
- GET /api/v1/users/{user_id}
- POST /api/v1/users/create?name=YourName

## Users API Behavior

The create endpoint simulates transient backend behavior using a circular status iterator:
- 201 Created
- 200 OK
- 503 Service Unavailable
- 504 Gateway Timeout
- then repeats from 201 again

Implementation reference: app/v1/api/users.py

This makes retry behavior predictable while avoiding list exhaustion.

## Retry Script

Run:

```bash
uv run scripts/users.py
```

What it does:
- Sends create-user requests for several names
- Retries retryable HTTP statuses
- Uses exponential backoff with jitter

Current formula in scripts/users.py:
- delay = base_delay * 2^(attempt - 1)
- jitter = random value in [0, 20% of delay]

With base_delay = 1.0, delays are approximately:
- attempt 1: 1.0s plus jitter
- attempt 2: 2.0s plus jitter
- attempt 3: 4.0s plus jitter

## Tests

```bash
uv run pytest -q
```

## Notes

- Users are stored in memory only and reset on restart.
- Retry tests are in tests/test_retry.py.
