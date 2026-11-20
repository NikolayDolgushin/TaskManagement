import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.projects.models import Project, ProjectMember, ProjectRole
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from sqlalchemy.orm import selectinload


async def create_project(
    db: AsyncSession,
    user: User,
    data: ProjectCreate,
) -> Project:
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=user.id,
    )

    db.add(project)
    await db.flush()

    membership = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectRole.OWNER,
    )

    db.add(membership)

    await db.commit()
    await db.refresh(project)

    return project


async def get_user_projects(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Project]:
    stmt = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user_id)
        .order_by(Project.created_at.desc())
    )

    result = await db.scalars(stmt)

    return list(result.all())


async def get_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Project | None:
    stmt = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(
            Project.id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    return await db.scalar(stmt)


async def update_project(
    db: AsyncSession,
    project: Project,
    data: ProjectUpdate,
) -> Project:
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project


async def delete_project(
    db: AsyncSession,
    project: Project,
) -> None:
    await db.delete(project)
    await db.commit()


async def get_project_members(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ProjectMember]:
    stmt = (
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.joined_at.asc())
    )

    result = await db.scalars(stmt)

    return list(result.all())


async def get_project_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProjectMember | None:
    stmt = (
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    return await db.scalar(stmt)


async def add_project_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProjectMember | None:
    user = await db.get(User, user_id)

    if user is None:
        raise ValueError("Пользователь не найден")

    existing_member = await get_project_member(
        db,
        project_id,
        user_id,
    )

    if existing_member is not None:
        raise ValueError("Пользователь уже состоит в проекте")

    membership = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=ProjectRole.MEMBER,
    )

    db.add(membership)
    await db.commit()

    return await get_project_member(
        db,
        project_id,
        user_id,
    )


async def remove_project_member(
    db: AsyncSession,
    membership: ProjectMember,
) -> None:
    await db.delete(membership)
    await db.commit()
