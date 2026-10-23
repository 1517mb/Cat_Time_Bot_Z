import pytest_asyncio
from core import models
from scripts import init_level
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def level_session_maker(monkeypatch):
    """Use an empty database so initialization must create its own schema."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(init_level, "async_session_maker", session_maker)
    try:
        yield session_maker
    finally:
        await engine.dispose()


async def test_init_levels_creates_schema_and_seeds_levels(level_session_maker):
    await init_level.init_levels()

    async with level_session_maker() as session:
        result = await session.execute(
            select(models.LevelTitle).order_by(models.LevelTitle.level)
        )
        levels = result.scalars().all()

    assert [level.level for level in levels] == list(range(1, 101))
    assert all(level.title == init_level.LEVEL_TITLES_DATA[level.level][0]
               for level in levels)
    assert all(level.category == init_level.LEVEL_TITLES_DATA[level.level][1]
               for level in levels)
    assert levels[0].min_experience == 0
    assert levels[9].min_experience == 270
    assert levels[39].min_experience == 1770
    assert levels[-1].min_experience == 6570


async def test_init_levels_can_be_repeated_without_duplicates(level_session_maker):
    await init_level.init_levels()
    async with level_session_maker() as session:
        first = await session.scalar(
            select(models.LevelTitle).where(models.LevelTitle.level == 1)
        )
        first.title = "Outdated title"
        first.min_experience = 999
        session.add(models.LevelTitle(
            level=101, title="Obsolete", category="legend", min_experience=9999
        ))
        await session.commit()

    await init_level.init_levels()

    async with level_session_maker() as session:
        levels = (await session.scalars(
            select(models.LevelTitle).order_by(models.LevelTitle.level)
        )).all()

    assert [level.level for level in levels] == list(range(1, 101))
    assert levels[0].title == init_level.LEVEL_TITLES_DATA[1][0]
    assert levels[0].min_experience == 0
