import datetime
from typing import Optional, Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core import models


async def get_company_by_name(
        session: AsyncSession, name: str) -> Optional[models.Company]:
    stmt = select(models.Company).where(models.Company.name == name)
    return await session.scalar(stmt)


async def get_similar_companies(
        session: AsyncSession, name: str) -> Sequence[str]:
    stmt = select(models.Company.name).where(
        models.Company.name.ilike(f"%{name}%"))
    result = await session.scalars(stmt)
    return result.all()


async def create_company(session: AsyncSession, name: str) -> models.Company:
    company = models.Company(name=name)
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def get_active_activity(
        session: AsyncSession, user_id: int) -> Optional[models.UserActivity]:
    """Возвращает текущий незавершенный выезд пользователя"""
    stmt = select(models.UserActivity).where(
        and_(
            models.UserActivity.user_id == user_id,
            models.UserActivity.leave_time.is_(None)
        )
    ).order_by(models.UserActivity.join_time.desc())
    return await session.scalar(stmt)


async def create_activity(session: AsyncSession,
                          user_id: int, username:
                          str, company_id: int) -> models.UserActivity:
    activity = models.UserActivity(
        user_id=user_id,
        username=username,
        company_id=company_id
    )
    session.add(activity)
    await session.commit()
    await session.refresh(activity)
    return activity


async def get_today_trips_count(session: AsyncSession, user_id: int) -> int:
    """Считает количество выездов за сегодня"""
    today = datetime.datetime.now().date()
    stmt = select(func.count()).select_from(models.UserActivity).where(
        and_(
            models.UserActivity.user_id == user_id,
            func.date(models.UserActivity.join_time) == today
        )
    )
    return await session.scalar(stmt) or 0


async def create_achievements_bulk(session: AsyncSession,
                                   achievements_data: list[dict]):
    """Массовое создание ачивок"""
    if not achievements_data:
        return
    achievements = [models.Achievement(**data) for data in achievements_data]
    session.add_all(achievements)
    await session.commit()
