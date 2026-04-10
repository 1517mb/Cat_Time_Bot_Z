from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str


class CompanyResponse(CompanyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ActivityCreate(BaseModel):
    user_id: int
    username: Optional[str] = None
    company_id: int


class ActivityUpdate(BaseModel):
    leave_time: datetime
    experience_gained: int = 0
    edited: bool = False
    edit_count: int = 0


class ActivityResponse(ActivityCreate):
    id: int
    join_time: datetime
    leave_time: Optional[datetime] = None
    experience_gained: int
    model_config = ConfigDict(from_attributes=True)


class SeasonRankResponse(BaseModel):
    id: int
    user_id: int
    season_id: int
    experience: int
    level: int
    visits_count: int
    model_config = ConfigDict(
        from_attributes=True)
