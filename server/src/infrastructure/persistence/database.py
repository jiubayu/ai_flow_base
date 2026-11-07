from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import Config

SessionFactory = sessionmaker[Session]


def create_database_engine(config: Config) -> Engine:
    return create_engine(config.database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker(bind=engine, expire_on_commit=False)
