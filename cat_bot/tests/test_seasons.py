import datetime

from core import models
from services.seasons import create_season_if_needed


async def test_season_creation_and_rotation(db_session):
    """Тест: проверяем создание первого сезона и защиту от дубликатов"""
    season1, is_new1 = await create_season_if_needed(db_session)
    assert is_new1 is True
    assert season1.is_active is True
    assert season1.name is not None
    assert season1.end_date is not None
    today = datetime.datetime.now().date()
    end_date = season1.end_date.date() if isinstance(
        season1.end_date, datetime.datetime) else season1.end_date
    assert end_date > today
    season2, is_new2 = await create_season_if_needed(db_session)
    assert is_new2 is False
    assert season1.id == season2.id


async def test_season_expiration_time_machine(db_session):
    """Тест-машина времени: проверяем закрытие просроченного сезона"""
    today = datetime.datetime.now().date()
    past_date = today - datetime.timedelta(days=5)
    old_season = models.Season(
        name="Старый просроченный сезон",
        theme="winter",
        start_date=past_date - datetime.timedelta(days=90),
        end_date=past_date,
        is_active=True
    )
    db_session.add(old_season)
    await db_session.commit()
    old_season_id = old_season.id
    new_season, is_new = await create_season_if_needed(db_session)
    assert is_new is True
    assert new_season.id != old_season_id
    assert new_season.is_active is True
    await db_session.refresh(old_season)
    assert old_season.is_active is False
