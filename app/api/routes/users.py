from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    UserAdminRead,
    UserPublic,
    UserRead,
    UserRoleUpdate,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.users import (
    change_user_password,
    deactivate_user,
    get_user_by_id,
    get_users,
    update_user,
    update_user_role,
    update_user_status,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Получение собственного профиля",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Обновление собственного профиля",
)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await update_user(
        db=db,
        user=current_user,
        user_data=user_data,
    )


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Изменение собственного пароля",
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await change_user_password(
        db=db,
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )


@router.get(
    "",
    response_model=list[UserPublic],
    summary="Список пользователей",
)
async def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[User]:
    return await get_users(
        db=db,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    summary="Получение публичного профиля пользователя",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    user = await get_user_by_id(db, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    return user


@router.patch(
    "/{user_id}/status",
    response_model=UserAdminRead,
    summary="Изменение статуса пользователя",
)
async def change_user_status(
    user_id: UUID,
    status_data: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> User:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if user.id == admin.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя заблокировать собственный аккаунт",
        )

    return await update_user_status(
        db=db,
        user=user,
        is_active=status_data.is_active,
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserAdminRead,
    summary="Изменение глобальной роли пользователя",
)
async def change_user_role(
    user_id: UUID,
    role_data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> User:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if user.id == admin.id and role_data.role != admin.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить собственную роль",
        )

    return await update_user_role(
        db=db,
        user=user,
        role=role_data.role,
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Деактивация собственного аккаунта",
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await deactivate_user(
        db=db,
        user=current_user,
    )
