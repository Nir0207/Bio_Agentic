from typing import Generator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.answering_service import AnsweringService
from app.services.auth_service import AuthService
from app.services.orchestration_service import OrchestrationService
from app.services.verification_service import VerificationService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = decode_access_token(token)
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise DomainError(code='unauthorized', message='User not found for token.', status_code=401)
    return user


def get_orchestration_service() -> OrchestrationService:
    return OrchestrationService()


def get_verification_service() -> VerificationService:
    return VerificationService()


def get_answering_service() -> AnsweringService:
    return AnsweringService()
