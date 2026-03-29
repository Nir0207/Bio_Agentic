from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

if settings.sqlite_db_path.startswith('sqlite:///'):
    sqlite_file = settings.sqlite_db_path.replace('sqlite:///', '', 1)
    db_path = Path(sqlite_file)
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.sqlite_db_path,
    connect_args={'check_same_thread': False} if settings.sqlite_db_path.startswith('sqlite') else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
