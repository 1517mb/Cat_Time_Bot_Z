import datetime

from core import crud, models


async def test_get_next_level_exp(db_session):
    """Тест: проверяем, что бот правильно отдает порог опыта для следующего уровня"""  # noqa: E501
    lvl1 = models.LevelTitle(
        level=1,
        title="Человек, который видел Wi-Fi",
        category="beginner",
        min_experience=0
    )
    lvl2 = models.LevelTitle(
        level=2,
        title="Укротитель USB",
        category="beginner",
        min_experience=30
    )
    db_session.add_all([lvl1, lvl2])
    await db_session.commit()
    next_exp = await crud.get_next_level_exp(db_session, current_level=1)
    assert next_exp == 30


async def test_user_rank_info_creation(db_session):
    """Тест: проверяем связь ранга с сезоном и титулом"""
    user_id = 999
    season = models.Season(name="Тестовый Сезон", is_active=True)
    lvl1 = models.LevelTitle(
        level=1,
        title="Новичок",
        category="beginner",
        min_experience=0
    )
    db_session.add_all([season, lvl1])
    await db_session.commit()
    rank = models.SeasonRank(
        user_id=user_id,
        season_id=season.id,
        level=1,
        experience=10,
        level_title_id=lvl1.id
    )
    db_session.add(rank)
    await db_session.commit()
    user_rank = await crud.get_user_rank_info(db_session, user_id)
    assert user_rank is not None
    assert user_rank.experience == 10
    assert user_rank.level == 1
    assert user_rank.level_title is not None
    assert user_rank.level_title.title is not None
    assert user_rank.level_title.title == "Новичок"


async def test_update_user_rank_level_up(db_session):
    """Тест: проверяем начисление опыта и повышение уровня при /leave"""
    user_id = 111
    username = "admin"
    season = models.Season(name="Тестовый Сезон", is_active=True)
    lvl1 = models.LevelTitle(
        level=1, title="Новичок", category="beg", min_experience=0
    )
    lvl2 = models.LevelTitle(
        level=2, title="Бывалый", category="beg", min_experience=50
    )
    db_session.add_all([season, lvl1, lvl2])
    await db_session.commit()
    time_spent = datetime.timedelta(hours=1)
    rank, is_level_up, new_lvl = await crud.update_user_rank(
        session=db_session,
        user_id=user_id,
        username=username,
        exp_added=30,
        time_added=time_spent
    )
    assert is_level_up is False
    assert new_lvl == 1
    assert rank is not None
    assert rank.experience == 30
    rank, is_level_up, new_lvl = await crud.update_user_rank(
        session=db_session,
        user_id=user_id,
        username=username,
        exp_added=30,
        time_added=time_spent
    )

    assert is_level_up is True
    assert new_lvl == 2
    assert rank is not None
    assert rank.experience == 60
    assert rank.level == 2
    assert rank.level_title_id == lvl2.id
