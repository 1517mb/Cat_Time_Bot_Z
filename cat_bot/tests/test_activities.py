
import datetime

from core import crud, models


async def test_join_and_active_activity(db_session):
    """Тест: создание выезда и проверка 'активного' статуса"""
    user_id = 12345
    username = "admin_skuf"
    company = await crud.create_company(db_session, "ООО Рога и Копыта")
    active_before = await crud.get_active_activity(db_session, user_id)
    assert active_before is None
    await crud.create_activity(db_session, user_id, username, company.id)
    active_after = await crud.get_active_activity(db_session, user_id)
    assert active_after is not None
    assert active_after.company_id == company.id
    assert active_after.leave_time is None


async def test_today_trips_count(db_session):
    """Тест: проверка счетчика выездов за сегодня"""
    user_id = 777
    username = "hardworker"
    company = await crud.create_company(db_session, "ЗАО Вектор")
    activity1 = models.UserActivity(
        user_id=user_id,
        username=username,
        company_id=company.id,
        join_time=datetime.datetime.now() - datetime.timedelta(hours=2),
        leave_time=datetime.datetime.now() - datetime.timedelta(hours=1)
    )
    activity2 = models.UserActivity(
        user_id=user_id,
        username=username,
        company_id=company.id,
        join_time=datetime.datetime.now() - datetime.timedelta(minutes=30),
    )
    db_session.add_all([activity1, activity2])
    activity_yesterday = models.UserActivity(
        user_id=user_id,
        username=username,
        company_id=company.id,
        join_time=datetime.datetime.now() - datetime.timedelta(
            days=1, hours=2),
        leave_time=datetime.datetime.now() - datetime.timedelta(
            days=1, hours=1)
    )
    db_session.add(activity_yesterday)
    await db_session.commit()
    count = await crud.get_today_trips_count(db_session, user_id)
    assert count == 2
