from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin
from app.services.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await register_user(
        db=db,
        user_data=user_data,
    )

    access_token = create_access_token(user_id=user.id)

    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Авторизация пользователя",
)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await authenticate_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id)

    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из аккаунта",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> None:
    # JWT пока не отзывается сервером.
    # Клиент должен удалить сохраненный access_token.
    return None
