from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import GlobalRole, User
from app.schemas.user import UserCreate, UserUpdate


async def register_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    email = str(user_data.email).lower()

    existing_user = await db.scalar(select(User).where(User.email == email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    user = User(
        email=email,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name.strip(),
        last_name=user_data.last_name.strip(),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    email = email.lower()

    user = await db.scalar(select(User).where(User.email == email))

    if user is None or not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


async def update_user(
    db: AsyncSession,
    user: User,
    user_data: UserUpdate,
) -> User:
    updates = user_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if value is not None:
            setattr(user, field, value.strip())

    await db.commit()
    await db.refresh(user)

    return user


async def change_user_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текущий пароль указан неверно",
        )

    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль должен отличаться от текущего",
        )

    user.password_hash = hash_password(new_password)

    await db.commit()


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID,
) -> User | None:
    return await db.get(User, user_id)


async def get_users(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 20,
) -> list[User]:
    result = await db.scalars(
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.last_name, User.first_name)
        .offset(offset)
        .limit(limit)
    )

    return list(result.all())


async def update_user_status(
    db: AsyncSession,
    user: User,
    is_active: bool,
) -> User:
    user.is_active = is_active

    await db.commit()
    await db.refresh(user)

    return user


async def update_user_role(
    db: AsyncSession,
    user: User,
    role: GlobalRole,
) -> User:
    user.role = role

    await db.commit()
    await db.refresh(user)

    return user


async def deactivate_user(
    db: AsyncSession,
    user: User,
) -> None:
    # Пока не удаляем запись физически.
    # Это важно, поскольку в будущем пользователь может
    # быть связан с проектами и задачами.
    user.is_active = False

    await db.commit()
