# FinPilot — Smart Expense & Personal Finance Management

A full-stack personal finance application built with **Python, FastAPI, PostgreSQL, SQLAlchemy, JWT, and vanilla JavaScript**. It includes secure user accounts, transaction management, budgets, analytics, CSV import/export, recurring transaction generation, PDF reports, tests, and Docker support.

> This is a portfolio/learning project. It is not a banking application and does not connect to financial institutions.

## Features

- JWT authentication with Argon2 password hashing
- Per-user data isolation
- Income and expense CRUD with category validation
- Search, filtering, pagination, CSV import and export
- Monthly budgets with 80% and 100% threshold status
- Monthly summary, category breakdown and six-month cash-flow chart
- Three-month moving-average expense forecast
- Idempotent recurring transaction generation
- Downloadable monthly PDF statement
- Pytest API tests
- Docker Compose with PostgreSQL

## Architecture

- `app/routers`: HTTP/API layer
- `app/models.py`: SQLAlchemy relational models
- `app/schemas.py`: Pydantic request/response validation
- `app/security.py`: password hashing and JWT
- `app/database.py`: database engine/session lifecycle
- `frontend/`: responsive browser interface

## Requirements

- Python 3.11+
- pip
- Optional: Docker Desktop / Docker Engine

## Run locally (SQLite)

1. Create and activate a virtual environment:

   **macOS/Linux**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`. Set a strong `SECRET_KEY` before using the app beyond local development. The default database is SQLite.

4. Start the server:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Open [http://localhost:8000](http://localhost:8000). API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Run with Docker and PostgreSQL

```bash
docker compose up --build
```

Open http://localhost:8000. Stop with `docker compose down`; persistent PostgreSQL data remains in the named volume. To remove the volume too, use `docker compose down -v`.

**Production note:** replace the example database password and secret key, use HTTPS, configure trusted CORS origins, add a reverse proxy, backups, migrations, and centralized logging before deployment.

## Run tests

```bash
pytest -q
```

Tests use an isolated SQLite database configured in `tests/conftest.py`.

## API overview

All endpoints except health and registration/login require `Authorization: Bearer <access_token>`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT |
| GET | `/api/auth/me` | Current user |
| GET/POST | `/api/categories` | List/create categories |
| GET/POST | `/api/transactions` | List/create transactions |
| PUT/DELETE | `/api/transactions/{id}` | Update/delete transaction |
| GET | `/api/transactions/export.csv` | Export CSV |
| POST | `/api/transactions/import.csv` | Import CSV |
| GET/POST | `/api/budgets` | List/create monthly budgets |
| DELETE | `/api/budgets/{id}` | Delete budget |
| GET | `/api/analytics/summary` | Monthly KPIs and category totals |
| GET | `/api/analytics/trend` | Monthly income/expense trend |
| GET | `/api/analytics/forecast` | Moving-average estimate |
| GET | `/api/reports/monthly.pdf` | Download PDF report |
| POST | `/api/recurring/generate` | Generate this month's recurring entries |

## Example API workflow

1. Register using `POST /api/auth/register`.
2. Log in using `POST /api/auth/login` and copy `access_token`.
3. Click **Authorize** in Swagger and paste the access token; Swagger applies the Bearer scheme.
4. Create a transaction using `POST /api/transactions`:

```json
{
  "kind": "expense",
  "amount": 420.50,
  "description": "Groceries",
  "transaction_date": "2026-11-12",
  "category_id": 3,
  "recurring": false
}
```

Use a category ID returned by `GET /api/categories` for the authenticated user.

## Data model

- User 1—many Transactions
- User 1—many Categories
- User 1—many Budgets
- Category 1—many Transactions
- Category optionally associated with Budgets

## Important implementation notes / next improvements

- `Base.metadata.create_all()` is used for quick local startup. For team/production workflows, introduce Alembic migrations.
- Recurring generation is triggered manually and creates one copy per template per month; production systems should use a scheduler/worker and define billing-day and end-of-month behavior.
- Forecasting is a transparent three-month moving average, not a machine-learning model.
- For multi-currency support, store currency codes and use decimal/numeric database types rather than floating-point amounts.
- For production-grade reliability, use `Decimal`/`NUMERIC` for money, add rate limiting, refresh-token rotation, audit logs, stronger CSV import validation, and integration tests against PostgreSQL.
- Consider adding CI with GitHub Actions and deployment to a managed platform.

## Suggested GitHub repository description

`Full-stack personal finance management platform built with FastAPI, PostgreSQL, JWT authentication, budgeting, analytics, recurring transactions and PDF reporting.`

## License

MIT — add a LICENSE file if you intend to publish this repository under the MIT License.
