"""SQLAlchemy ORM models for normalized GarminCoach storage."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from backend.app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    garmin_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    garmin_password: Mapped[str] = mapped_column(Text, nullable=False)
    is_cn: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    daily_summaries: Mapped[list[GarminDailySummary]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list[Activity]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    training_plans: Mapped[list[TrainingPlan]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[list[DailyAnalysis]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    profiles: Mapped[list["UserProfile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    coach_memories: Mapped[list["CoachMemory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    injury_logs: Mapped[list["InjuryLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    weekly_reports: Mapped[list["WeeklyReport"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    home_summary: Mapped[Optional["HomeSummary"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )


class HomeSummary(Base):
    __tablename__ = "home_summaries"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_home_summary_user"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    latest_run_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    week_stats_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    month_stats_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    ai_brief_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="home_summary")


class GarminDailySummary(Base):
    __tablename__ = "garmin_daily_summaries"
    __table_args__ = (
        UniqueConstraint("user_id", "summary_date", name="uq_daily_summary_user_date"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Sleep
    sleep_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    sleep_time_hours: Mapped[Optional[float]] = mapped_column(Float)
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer)
    deep_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    rem_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    light_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    awake_sleep_seconds: Mapped[Optional[float]] = mapped_column(Float)
    recovery_quality_percent: Mapped[Optional[float]] = mapped_column(Float)

    # Health
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery_charged: Mapped[Optional[int]] = mapped_column(Integer)
    body_battery_drained: Mapped[Optional[int]] = mapped_column(Integer)
    average_stress_level: Mapped[Optional[int]] = mapped_column(Integer)
    stress_qualifier: Mapped[Optional[str]] = mapped_column(String(64))
    hrv_status: Mapped[Optional[str]] = mapped_column(String(64))

    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="daily_summaries")


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint("user_id", "garmin_activity_id", name="uq_activity_user_garmin_id"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    garmin_activity_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    activity_date: Mapped[Optional[date]] = mapped_column(Date)
    type: Mapped[Optional[str]] = mapped_column(String(64))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    start_time_local: Mapped[Optional[datetime]] = mapped_column(DateTime)

    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    average_pace_seconds: Mapped[Optional[float]] = mapped_column(Float)  # seconds / km

    average_hr: Mapped[Optional[int]] = mapped_column(Integer)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer)
    calories: Mapped[Optional[int]] = mapped_column(Integer)

    average_cadence: Mapped[Optional[int]] = mapped_column(Integer)
    average_stride_length_cm: Mapped[Optional[float]] = mapped_column(Float)
    average_ground_contact_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    average_vertical_oscillation_cm: Mapped[Optional[float]] = mapped_column(Float)
    average_vertical_ratio_percent: Mapped[Optional[float]] = mapped_column(Float)

    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="activities")
    laps: Mapped[list[ActivityLap]] = relationship(
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="ActivityLap.lap_index",
    )


class ActivityLap(Base):
    __tablename__ = "activity_laps"
    __table_args__ = (
        UniqueConstraint("activity_id", "lap_index", name="uq_activity_lap_activity_index"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)

    lap_index: Mapped[int] = mapped_column(Integer, nullable=False)

    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    pace_seconds: Mapped[Optional[float]] = mapped_column(Float)  # seconds / km

    average_hr: Mapped[Optional[int]] = mapped_column(Integer)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer)

    cadence: Mapped[Optional[int]] = mapped_column(Integer)
    stride_length_cm: Mapped[Optional[float]] = mapped_column(Float)
    ground_contact_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    vertical_oscillation_cm: Mapped[Optional[float]] = mapped_column(Float)
    vertical_ratio_percent: Mapped[Optional[float]] = mapped_column(Float)

    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    activity: Mapped[Activity] = relationship(back_populates="laps")


class TrainingPlan(Base):
    __tablename__ = "training_plans"
    __table_args__ = (
        UniqueConstraint("user_id", "plan_date", "workout_name", name="uq_plan_user_date_name"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)

    workout_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="training_plans")


class DailyAnalysis(Base):
    __tablename__ = "daily_analyses"
    __table_args__ = (
        UniqueConstraint("user_id", "analysis_date", name="uq_analysis_user_date"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)

    raw_data_summary_md: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    ai_advice_md: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    charts_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    model_name: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="success")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="analyses")


class UserProfile(Base):
    """用户个人基础数据档案"""
    __tablename__ = "user_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "profile_date", name="uq_user_profile_date"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_date: Mapped[date] = mapped_column(Date, nullable=False)

    # 身体成分
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    bmi: Mapped[Optional[float]] = mapped_column(Float)
    body_fat_percent: Mapped[Optional[float]] = mapped_column(Float)

    # 运动能力
    vo2_max: Mapped[Optional[float]] = mapped_column(Float)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)

    # 训练状态
    training_status: Mapped[Optional[str]] = mapped_column(String(64))
    training_effect: Mapped[Optional[float]] = mapped_column(Float)
    activity_effect: Mapped[Optional[float]] = mapped_column(Float)

    # 训练准备度
    training_readiness: Mapped[Optional[int]] = mapped_column(Integer)

    # 心率区间 JSON
    heart_rate_zones_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    # 个人最佳记录 JSON
    personal_records_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    # 比赛预测 JSON
    race_predictions_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    # 原始数据
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="profiles")


class ChatMessage(Base):
    """聊天消息记录"""
    __tablename__ = "chat_messages"
    __table_args__ = {"mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wechat_user_id: Mapped[int] = mapped_column(ForeignKey("wechat_users.id", ondelete="CASCADE"), nullable=False)

    # 消息角色和内容
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(LONGTEXT, nullable=False)

    # 上下文信息
    context_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    wechat_user: Mapped[WechatUser] = relationship(back_populates="chat_messages")


class CoachMemory(Base):
    """运动员档案（教练记忆）"""
    __tablename__ = "coach_memories"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_coach_memory_user"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 目标赛事
    target_race: Mapped[Optional[str]] = mapped_column(String(255))  # 例: "2026上海马拉松"
    target_race_date: Mapped[Optional[date]] = mapped_column(Date)
    target_race_distance_km: Mapped[Optional[float]] = mapped_column(Float)  # 例: 42.195

    # 个人最佳
    pb_5k_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    pb_10k_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    pb_half_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    pb_full_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # 训练目标
    weekly_mileage_goal_km: Mapped[Optional[float]] = mapped_column(Float)  # 周跑量目标
    target_finish_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)  # 目标完赛时间

    # 自由备注（教练可补充）
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # 生理指标
    max_hr: Mapped[Optional[int]] = mapped_column(Integer)  # 最大心率
    rest_hr: Mapped[Optional[int]] = mapped_column(Integer)  # 静息心率
    vo2max: Mapped[Optional[float]] = mapped_column(Float)  # 最大摄氧量
    lthr: Mapped[Optional[int]] = mapped_column(Integer)  # 乳酸阈心率
    ftp: Mapped[Optional[int]] = mapped_column(Integer)  # 功能性阈值功率

    # 扩展信息
    injury_history: Mapped[Optional[str]] = mapped_column(Text)  # 历史伤病
    training_preference: Mapped[Optional[str]] = mapped_column(Text)  # 训练偏好

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="coach_memories")


class InjuryLog(Base):
    """伤病日志"""
    __tablename__ = "injury_logs"
    __table_args__ = {"mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    body_part: Mapped[str] = mapped_column(String(64), nullable=False)  # 例: "左膝", "右跟腱"
    injury_type: Mapped[Optional[str]] = mapped_column(String(64))  # 伤病类型，例: "疲劳性骨折"
    pain_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-10
    description: Mapped[Optional[str]] = mapped_column(Text)  # 详细描述
    is_resolved: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)  # 是否已恢复

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="injury_logs")


class WeeklyReport(Base):
    """周度总结报告"""
    __tablename__ = "weekly_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start_date", name="uq_weekly_report_user_week"),
        {"mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)  # 周一日期
    week_end_date: Mapped[date] = mapped_column(Date, nullable=False)  # 周日日期

    # 统计指标
    total_distance_km: Mapped[Optional[float]] = mapped_column(Float)
    total_duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    run_count: Mapped[Optional[int]] = mapped_column(Integer)
    avg_pace_seconds: Mapped[Optional[float]] = mapped_column(Float)  # 均配（秒/公里）

    # 负荷与信心
    acwr: Mapped[Optional[float]] = mapped_column(Float)  # 急慢性负荷比
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)  # 比赛信心评分 0-100

    # AI 总结
    ai_summary: Mapped[Optional[str]] = mapped_column(LONGTEXT)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="weekly_reports")
