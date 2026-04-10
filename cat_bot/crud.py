from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

import cat_bot.core.models as models
import schemas


async def get_company_by_name(
        session: AsyncSession, name: str) -> Optional[models.Company]:
    """Аналог Company.objects.filter(name=name).first()"""
    stmt = select(models.Company).where(models.Company.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_company(session: AsyncSession, name: str) -> models.Company:
    """Аналог Company.objects.create(...)"""
    new_company = models.Company(name=name)
    session.add(new_company)
    await session.commit()
    await session.refresh(new_company)
    return new_company


async def get_similar_companies(
        session: AsyncSession, search_term: str) -> List[str]:
    """Аналог Company.objects.filter(name__icontains=...)"""
    stmt = select(models.Company.name).where(
        models.Company.name.ilike(f"%{search_term}%"))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_active_activity(
        session: AsyncSession, user_id: int) -> Optional[models.UserActivity]:
    """Ищет незакрытый выезд пользователя"""
    stmt = select(models.UserActivity).where(
        models.UserActivity.user_id == user_id,
        models.UserActivity.leave_time.is_(None)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_activity(
        session: AsyncSession,
        activity_data: schemas.ActivityCreate) -> models.UserActivity:
    """Создает новый выезд (команда /join)"""
    new_activity = models.UserActivity(**activity_data.model_dump())
    session.add(new_activity)
    await session.commit()
    await session.refresh(new_activity)
    return new_activity


async def get_today_trips_count(session: AsyncSession, user_id: int) -> int:
    """Аналог UserActivity.objects.filter(join_time__date=today).count()"""
    today = func.date('now', 'localtime')
    stmt = select(func.count()).select_from(models.UserActivity).where(
        models.UserActivity.user_id == user_id,
        func.date(models.UserActivity.join_time) == today
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def create_achievement(session: AsyncSession,
                             user_id: int,
                             username: str, name: str):
    """Выдача ачивки"""
    ach = models.Achievement(user_id=user_id,
                             username=username,
                             achievement_name=name)
    session.add(ach)
    await session.commit()
