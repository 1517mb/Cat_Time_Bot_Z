import datetime
from typing import List, Optional

from sqlalchemy import (Boolean, DateTime, ForeignKey, Index, Integer,
                        Interval, Numeric, String, Text, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    activities: Mapped[List["UserActivity"]] = relationship(
        back_populates="company")

    def __str__(self) -> str:
        return self.name


class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"))
    join_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    leave_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True))
    edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edit_count: Mapped[int] = mapped_column(Integer, default=0)
    experience_gained: Mapped[int] = mapped_column(Integer, default=0)

    company: Mapped["Company"] = relationship(back_populates="activities")

    @property
    def get_spent_time(self) -> str:
        if self.leave_time:
            leave = self.leave_time.replace(tzinfo=None)
            join = self.join_time.replace(tzinfo=None)
            delta = leave - join
            total_seconds = delta.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            if hours < 1:
                return f"{minutes} мин."
            return f"{hours} ч. {minutes} мин."
        return "Ещё не покинул"


class LevelTitle(Base):
    __tablename__ = "level_titles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(20), default="beginner")
    min_experience: Mapped[int] = mapped_column(Integer, default=0)

    season_ranks: Mapped[List["SeasonRank"]] = relationship(
        back_populates="level_title")
    user_ranks: Mapped[List["UserRank"]] = relationship(
        back_populates="level_title")


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    theme: Mapped[str] = mapped_column(String(20), default="winter")
    start_date: Mapped[datetime.date] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[Optional[datetime.date]] = mapped_column(
        DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    ranks: Mapped[List["SeasonRank"]] = relationship(back_populates="season")


class SeasonRank(Base):
    __tablename__ = "season_ranks"
    __table_args__ = (
        UniqueConstraint("user_id", "season_id", name="uix_user_season"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"))
    experience: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    total_time: Mapped[datetime.timedelta] = mapped_column(
        Interval, default=datetime.timedelta())
    visits_count: Mapped[int] = mapped_column(Integer, default=0)
    level_title_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("level_titles.id", ondelete="SET NULL"))
    achieved_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())

    season: Mapped["Season"] = relationship(back_populates="ranks")
    level_title: Mapped[Optional["LevelTitle"]] = relationship(
        back_populates="season_ranks")


class UserRank(Base):
    __tablename__ = "user_ranks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    total_time: Mapped[datetime.timedelta] = mapped_column(
        Interval, default=datetime.timedelta())
    visits_count: Mapped[int] = mapped_column(Integer, default=0)
    level_title_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("level_titles.id", ondelete="SET NULL"))

    level_title: Mapped[Optional["LevelTitle"]] = relationship(
        back_populates="user_ranks")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String(255))
    achievement_name: Mapped[str] = mapped_column(String(255))
    achieved_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())


class DailyStatistics(Base):
    __tablename__ = "daily_statistics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime.date] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    total_time: Mapped[datetime.timedelta] = mapped_column(Interval)
    total_trips: Mapped[int] = mapped_column(Integer)


class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    __table_args__ = (
        Index("ix_currency_date", "currency", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    currency: Mapped[str] = mapped_column(String(15))
    rate: Mapped[float] = mapped_column(Numeric(20, 10))
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
