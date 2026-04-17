from core import crud, models
from sqlalchemy import select


async def test_create_company(db_session):
    """Тест: проверяем, что организация успешно создается в БД"""
    company_name = "ООО Рога и Копыта"
    new_company = await crud.create_company(db_session, company_name)
    assert new_company is not None
    assert new_company.name == company_name

    stmt = select(models.Company).where(models.Company.name == company_name)
    result = await db_session.scalar(stmt)
    assert result is not None
    assert result.id == new_company.id


async def test_get_similar_companies(db_session):
    """Тест: проверяем поиск похожих названий"""
    await crud.create_company(db_session, "Альфа Строй")
    await crud.create_company(db_session, "Альфа Банк")
    await crud.create_company(db_session, "Омега")
    similar = await crud.get_similar_companies(db_session, "Альфа")
    assert len(similar) == 2
    assert "Альфа Строй" in similar
    assert "Альфа Банк" in similar
    assert "Омега" not in similar
