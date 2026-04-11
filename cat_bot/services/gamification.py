import datetime
import random

from sqlalchemy.ext.asyncio import AsyncSession

from core import models
from core.bot_constants import BotAchievementsCfg

ACHIEVEMENT_BONUSES = {
    "Первая кровь": 1,
    "Лучший сотрудник": 5,
    "Командный игрок": 5,
    "А можно мне ещё выезд?": 5,
    "Экономлю на пропуске": 5,
}


def calculate_experience(join_time: datetime.datetime,
                         leave_time: datetime.datetime,
                         daily_visits: int) -> int:
    """Твоя математика расчета опыта"""
    if leave_time < join_time:
        return 0

    base_exp = 10 + min(20, max(0, (daily_visits - 1)) * 5)
    total_minutes = (leave_time - join_time).total_seconds() / 60

    if total_minutes >= 721:
        return 0

    if total_minutes <= 40:
        time_exp = total_minutes * 0.12
    elif total_minutes <= 80:
        time_exp = 4.8 + (total_minutes - 40) * 0.28
    elif total_minutes <= 120:
        time_exp = 15.2 + (total_minutes - 80) * 0.12
    else:
        extra_time = total_minutes - 120
        time_exp = 20.0 + (extra_time ** 0.7) * 0.05

    return max(0, int(round(base_exp + time_exp)))


async def check_achievements(session: AsyncSession,
                             user_id: int, username:
                             str, activity: models.UserActivity) -> list[str]:
    """Проверка ачивок через SQLAlchemy"""
    new_achievements = []
    leave = activity.leave_time.replace(tzinfo=None)
    join = activity.join_time.replace(tzinfo=None)
    duration = (leave - join).total_seconds()

    for (min_val, max_val), titles in BotAchievementsCfg.DURATION_ACHIEVEMENTS.items():  # noqa: E501
        if min_val <= duration < max_val:
            new_achievements.append(random.choice(titles))
            break

    for ach_name in new_achievements:
        session.add(models.Achievement(
            user_id=user_id,
            username=username or f"user_{user_id}",
            achievement_name=ach_name
        ))
    return new_achievements
