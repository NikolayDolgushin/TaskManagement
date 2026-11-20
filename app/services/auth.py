from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.user import Token, UserCreate, UserLogin
from app.services.users import authenticate_user, register_user

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
        email=str(user_data.email),
        password=user_data.password,
    )

    if user is None:
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
