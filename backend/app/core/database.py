from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_db_url = settings.sqlalchemy_database_url
if (
    settings.app_env == "production"
    and "sslmode=" not in _db_url
    and "localhost" not in _db_url
    and "127.0.0.1" not in _db_url
):
    _db_url = _db_url + ("&" if "?" in _db_url else "?") + "sslmode=require"

engine = create_engine(
    _db_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
