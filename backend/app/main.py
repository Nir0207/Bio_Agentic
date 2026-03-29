from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import answering, auth, health, orchestration, verification
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, RequestLoggingMiddleware
from app.db.base import Base
from app.db.seed import seed_default_user
from app.db.session import SessionLocal, engine

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RequestLoggingMiddleware)

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(orchestration.router)
api_router.include_router(verification.router)
api_router.include_router(answering.router)
app.include_router(api_router)

register_exception_handlers(app)


@app.on_event('startup')
def startup_event() -> None:
    data_dir = Path('data')
    data_dir.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_default_user(session)
    finally:
        session.close()
