from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from operant.app import models  # noqa: F401  (garante que todos os modelos sejam registados)
from operant.app.core.config import settings
from operant.app.db.base import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Para facilitar o primeiro arranque em desenvolvimento/docker-compose,
# garantimos que o schema mínimo existe. Em produção real, usar apenas Alembic.
Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


