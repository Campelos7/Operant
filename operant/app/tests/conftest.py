from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from operant.app import models  # noqa: F401  (register models)
from operant.app.api import deps
from operant.app.core.config import settings
from operant.app.db.base import Base
from operant.app.main import create_app


def _test_database_url() -> str:
    return os.getenv("OPERANT_DATABASE_URL", settings.database_url)


@pytest.fixture(scope="session")
def engine():
    url = _test_database_url()
    # Safety net: prevent running tests against a non-test DB by accident.
    env = os.getenv("OPERANT_ENV", settings.env).lower()
    if env != "test" and "test" not in url:
        raise RuntimeError(
            "Configuração insegura: defina OPERANT_ENV=test e use um DB de testes (URL contendo 'test')."
        )
    eng = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_db_session():
        yield db

    app.dependency_overrides[deps.db_session] = override_db_session
    with TestClient(app) as c:
        yield c


