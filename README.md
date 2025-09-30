# Easy Estates API (FastAPI)

MVP scaffold: FastAPI + SQLAlchemy + Alembic + JWT-ready

- Run: `uvicorn app.main:app --reload`
- Migrate: `alembic upgrade head`
- Env: see `.env.sample`

## Deploying on Railway

1. Create a new service from this repository in your Railway project.
2. Add the required environment variables under **Variables** (at minimum `DATABASE_URL`, `JWT_SECRET`, and any S3/SendGrid keys you rely on).
3. Set the **Start Command** to `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` or leave it blank—Railway will read it from `Procfile`.
4. Provision a PostgreSQL database on Railway (or point `DATABASE_URL` to an existing instance) and run `alembic upgrade head` once to bootstrap the schema.
