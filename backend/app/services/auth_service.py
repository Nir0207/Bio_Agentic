from app.core.exceptions import DomainError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register(self, *, email: str, full_name: str, password: str):
        existing = self.user_repository.get_by_email(email)
        if existing:
            raise DomainError(code='email_exists', message='Email already registered.', status_code=409)

        hashed_password = hash_password(password)
        return self.user_repository.create(email=email, full_name=full_name, hashed_password=hashed_password)

    def login(self, *, email: str, password: str) -> tuple[str, object]:
        user = self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise DomainError(code='invalid_credentials', message='Invalid email or password.', status_code=401)

        token = create_access_token(subject=user.id)
        return token, user

    def get_user_by_id(self, user_id: str):
        return self.user_repository.get_by_id(user_id)
