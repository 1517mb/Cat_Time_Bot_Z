import datetime
from typing import Optional, Sequence

from core import models
from core.models import (Achievement, Season, UserActivity)
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


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


async def get_current_season(session: AsyncSession) -> Optional[models.Season]:
    """Ищет текущий активный сезон"""
    stmt = select(
        models.Season).where(models.Season.is_active == True)
    return await session.scalar(stmt)


async def update_user_rank(
    session: AsyncSession,
    user_id: int,
    username: str,
    exp_added: int,
    time_added: datetime.timedelta
) -> tuple[Optional[models.SeasonRank], bool, int]:
    """Обновляет опыт и выдает новые уровни."""
    season = await get_current_season(session)
    if not season:
        return None, False, 0

    stmt = select(models.SeasonRank).where(
        and_(
            models.SeasonRank.user_id == user_id,
            models.SeasonRank.season_id == season.id
        )
    )
    rank = await session.scalar(stmt)

    if not rank:
        rank = models.SeasonRank(
            user_id=user_id,
            username=username,
            season_id=season.id,
            experience=0,
            level=1,
            visits_count=0,
            total_time=datetime.timedelta()
        )
        session.add(rank)
    if rank.total_time is None:
        rank.total_time = datetime.timedelta()
    if rank.experience is None:
        rank.experience = 0
    if rank.visits_count is None:
        rank.visits_count = 0
    old_level = rank.level
    rank.experience += exp_added
    rank.total_time += time_added
    rank.visits_count += 1
    stmt_lvl = select(models.LevelTitle).where(
        models.LevelTitle.min_experience <= rank.experience
    ).order_by(models.LevelTitle.level.desc())
    correct_level = await session.scalar(stmt_lvl)
    level_up = False
    if correct_level and correct_level.level != rank.level:
        rank.level = correct_level.level
        rank.level_title_id = correct_level.id
        level_up = rank.level > old_level
    return rank, level_up, rank.level


async def get_total_trips_count(session: AsyncSession, user_id: int) -> int:
    """Считает общее количество всех выездов пользователя за все время."""
    stmt = select(func.count(models.UserActivity.id)).where(
        models.UserActivity.user_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_user_achievements(session: AsyncSession, user_id: int):
    """Возвращает список всех достижений пользователя."""
    stmt = select(models.Achievement).where(
        models.Achievement.user_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_user_rank_info(session: AsyncSession, user_id: int):
    """Получает информацию о ранге пользователя вместе с названием уровня."""
    stmt = select(models.SeasonRank).options(
        selectinload(models.SeasonRank.level_title)
    ).where(models.SeasonRank.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_next_level_exp(session: AsyncSession, current_level: int) -> int:
    """Возвращает min_experience для следующего уровня."""
    stmt = select(models.LevelTitle.min_experience).where(
        models.LevelTitle.level == current_level + 1
    )
    result = await session.execute(stmt)
    exp = result.scalar_one_or_none()
    return exp if exp is not None else 0


async def get_full_daily_stats(session: AsyncSession):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    stmt_exists = select(UserActivity).where(func.date(UserActivity.join_time) == today).limit(1)
    exists = await session.scalar(stmt_exists)
    if not exists:
        return None
    stmt_season = select(Season).where(Season.is_active == True)
    season = await session.scalar(stmt_season)
    stmt_exp = select(func.sum(UserActivity.experience_gained)).where(
        func.date(UserActivity.join_time) == today
    )
    total_exp_today = await session.scalar(stmt_exp) or 0
    stmt_user_acts = select(
        UserActivity.user_id,
        UserActivity.username,
        func.count(UserActivity.id).label("trips"),
        func.sum(
            func.julianday(UserActivity.leave_time) - func.julianday(UserActivity.join_time)
        ).label("total_days")
    ).where(
        and_(
            func.date(UserActivity.join_time) == today,
            UserActivity.leave_time.is_not(None)
        )
    ).group_by(UserActivity.user_id, UserActivity.username)
    user_results = await session.execute(stmt_user_acts)
    user_stats = user_results.all()
    stmt_ach = select(Achievement).where(func.date(Achievement.achieved_at) == today)
    ach_results = await session.execute(stmt_ach)
    ach_list = ach_results.scalars().all()

    return {
        "season": season,
        "total_exp_today": total_exp_today,
        "user_stats": user_stats,
        "achievements": ach_list,
        "today": today
    }
