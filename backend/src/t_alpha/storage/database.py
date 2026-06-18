from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from t_alpha.config import Settings
from t_alpha.storage.models import Base


def create_mysql_engine(settings: Settings):
    settings.validate_project_database()
    return create_engine(settings.mysql_url, pool_pre_ping=True, future=True)


def init_schema(engine) -> None:
    Base.metadata.create_all(engine)


def build_session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
