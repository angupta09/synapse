import pytest
from sqlalchemy import text

from app.db import SessionLocal, engine


@pytest.fixture(scope="session")
def db_available() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture()
def db_session(db_available):
    if not db_available:
        pytest.skip("Postgres not reachable — start it with `docker compose up -d`")
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
