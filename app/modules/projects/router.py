import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate, ProjectMemberRead, ProjectMemberAdd,
)
from app.modules.projects.service import (
    create_project,
    delete_project,
    get_project,
    get_user_projects,
    update_project, get_project_members, get_project_member, remove_project_member, add_project_member,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_endpoint(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await create_project(db, current_user, data)
    return project


@router.get(
    "/",
    response_model=list[ProjectRead],
)
async def get_projects_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = await get_user_projects(db, current_user.id)
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
)
async def get_project_endpoint(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id, current_user.id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )

    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
)
async def update_project_endpoint(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id, current_user.id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец может редактировать проект",
        )

    if "name" in data.model_fields_set and data.name is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Название проекта не может быть пустым",
        )

    project = await update_project(db, project, data)

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project_endpoint(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id, current_user.id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец может удалить проект",
        )

    await delete_project(db, project)

@router.get(
    "/{project_id}/members",
    response_model=list[ProjectMemberRead],
)
async def get_project_members_endpoint(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id, current_user.id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )

    members = await get_project_members(db, project_id)

    return [
        ProjectMemberRead(
            user_id=member.user.id,
            first_name=member.user.first_name,
            last_name=member.user.last_name,
            email=member.user.email,
            role=member.role.value,
            joined_at=member.joined_at,
        )
        for member in members
    ]

@router.get(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberRead,
)
async def get_project_member_endpoint(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id, current_user.id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )

    membership = await get_project_member(
        db,
        project_id,
        user_id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участник не найден",
        )

    return ProjectMemberRead(
        user_id=membership.user.id,
        first_name=membership.user.first_name,
        last_name=membership.user.last_name,
        email=membership.user.email,
        role=membership.role.value,
        joined_at=membership.joined_at,
    )

@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member_endpoint(
    project_id: uuid.UUID,
    data: ProjectMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id, current_user.id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец может добавлять участников",
        )

    if data.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Владелец уже состоит в проекте",
        )

    try:
        membership = await add_project_member(
            db,
            project_id,
            data.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if str(exc) == "Пользователь не найден"
            else status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return ProjectMemberRead(
        user_id=membership.user.id,
        first_name=membership.user.first_name,
        last_name=membership.user.last_name,
        email=membership.user.email,
        role=membership.role.value,
        joined_at=membership.joined_at,
    )

@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member_endpoint(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project(db, project_id, current_user.id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден",
        )

    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец может удалять участников",
        )

    if user_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Нельзя удалить владельца проекта",
        )

    membership = await get_project_member(
        db,
        project_id,
        user_id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участник не найден",
        )

    await remove_project_member(db, membership)