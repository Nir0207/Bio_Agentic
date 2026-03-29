from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)) -> UserResponse:
    user = auth_service.register(email=payload.email, full_name=payload.full_name, password=payload.password)
    return UserResponse(id=user.id, email=user.email, full_name=user.full_name)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    token, user = auth_service.login(email=payload.email, password=payload.password)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user.id, email=user.email, full_name=user.full_name),
    )


@router.get('/me', response_model=UserResponse)
def me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email, full_name=current_user.full_name)
