"""教练算法模块：ACWR（急慢性负荷比）+ 比赛信心评分。

参考 claude-fitness-cn 的设计：
- ACWR = ATL(7天) / CTL(28天)
- Session Load = RPE × 运动时长（分钟）
- 比赛信心 = 伤病(40%) + 负荷完成率(25%) + 竞技状态(25%) + 恢复质量(10%)
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.db.models import Activity, GarminDailySummary, InjuryLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RPE 估算
# ---------------------------------------------------------------------------


def estimate_rpe_from_hr(
    avg_hr: Optional[int],
    max_hr: Optional[int],
    duration_seconds: Optional[float],
) -> float:
    """根据心率数据估算 RPE（1-10 级）。

    如果无心率数据，返回默认值 5。
    使用 %HRmax 映射：
        <60%  → 2（恢复跑）
        60-70% → 3-4（轻松跑）
        70-80% → 5-6（中等强度）
        80-90% → 7-8（节奏跑 / 间歇）
        >90%  → 9-10（冲刺 / 比赛配速）
    """
    if avg_hr is None or max_hr is None or max_hr <= 0:
        return 5.0

    hr_pct = avg_hr / max_hr * 100

    if hr_pct < 60:
        return 2.0
    elif hr_pct < 65:
        return 3.0
    elif hr_pct < 70:
        return 4.0
    elif hr_pct < 75:
        return 5.0
    elif hr_pct < 80:
        return 6.0
    elif hr_pct < 85:
        return 7.0
    elif hr_pct < 90:
        return 8.0
    elif hr_pct < 95:
        return 9.0
    else:
        return 10.0


def calculate_session_load(
    rpe: float,
    duration_seconds: Optional[float],
) -> float:
    """Session Load = RPE × 时长（分钟）。"""
    if duration_seconds is None or duration_seconds <= 0:
        return 0.0
    duration_minutes = duration_seconds / 60.0
    return rpe * duration_minutes


# ---------------------------------------------------------------------------
# ACWR 计算
# ---------------------------------------------------------------------------


def _get_daily_loads(
    db: Session,
    *,
    user_id: int,
    end_date: date,
    days: int = 28,
    user_max_hr: Optional[int] = None,
) -> list[float]:
    """获取最近 N 天每天的 Session Load 总和。

    返回长度为 `days` 的列表，索引 0 = 最早一天，索引 -1 = end_date。
    """
    start = end_date - timedelta(days=days - 1)

    activities = (
        db.query(Activity)
        .filter(Activity.user_id == user_id)
        .filter(Activity.activity_date >= start)
        .filter(Activity.activity_date <= end_date)
        .all()
    )

    # 每天聚合
    daily: dict[date, float] = {}
    for act in activities:
        act_date = act.activity_date
        if act_date is None:
            continue

        effective_max_hr = user_max_hr or act.max_hr or 190
        rpe = estimate_rpe_from_hr(
            act.average_hr, effective_max_hr, act.duration_seconds
        )
        load = calculate_session_load(rpe, act.duration_seconds)

        daily[act_date] = daily.get(act_date, 0.0) + load

    # 转为有序列表
    result: list[float] = []
    for i in range(days):
        d = start + timedelta(days=i)
        result.append(daily.get(d, 0.0))

    return result


def calculate_acwr(
    db: Session,
    *,
    user_id: int,
    target_date: date,
    user_max_hr: Optional[int] = None,
) -> dict[str, Any]:
    """计算急慢性负荷比 (ACWR)。

    - ATL = 最近 7 天平均 Session Load
    - CTL = 最近 28 天平均 Session Load
    - ACWR = ATL / CTL

    返回：
    {
        "acwr": float,
        "atl": float,             # 急性负荷（7天均值）
        "ctl": float,             # 慢性负荷（28天均值）
        "zone": str,              # "undertraining" / "sweet_spot" / "caution" / "danger"
        "zone_label": str,        # 中文标签
        "daily_loads_7d": list,   # 最近 7 天每日负荷
    }
    """
    loads_28d = _get_daily_loads(
        db,
        user_id=user_id,
        end_date=target_date,
        days=28,
        user_max_hr=user_max_hr,
    )
    loads_7d = loads_28d[-7:]

    atl = sum(loads_7d) / 7.0 if loads_7d else 0.0
    ctl = sum(loads_28d) / 28.0 if loads_28d else 0.0

    if ctl < 1.0:
        # 慢性负荷接近 0，无法计算有意义的 ACWR
        acwr = 0.0
        zone = "insufficient_data"
        zone_label = "数据不足"
    else:
        acwr = atl / ctl

        if acwr < 0.8:
            zone = "undertraining"
            zone_label = "训练不足"
        elif acwr <= 1.3:
            zone = "sweet_spot"
            zone_label = "最佳负荷"
        elif acwr <= 1.5:
            zone = "caution"
            zone_label = "注意过量"
        else:
            zone = "danger"
            zone_label = "危险过量"

    return {
        "acwr": round(acwr, 2),
        "atl": round(atl, 1),
        "ctl": round(ctl, 1),
        "zone": zone,
        "zone_label": zone_label,
        "daily_loads_7d": [round(x, 1) for x in loads_7d],
    }


# ---------------------------------------------------------------------------
# 比赛信心评分
# ---------------------------------------------------------------------------


def calculate_confidence_score(
    db: Session,
    *,
    user_id: int,
    target_date: date,
    weekly_mileage_goal_km: Optional[float] = None,
    user_max_hr: Optional[int] = None,
) -> dict[str, Any]:
    """计算比赛信心评分 (0-100)。

    权重分配：
    - 伤病状态: 40%（无伤=满分，有未恢复伤病根据疼痛等级扣分）
    - 负荷完成率: 25%（实际周跑量 / 目标周跑量）
    - 竞技状态: 25%（基于 ACWR 是否在 sweet spot）
    - 恢复质量: 10%（基于最近 3 天睡眠评分和身体电量）

    返回：
    {
        "score": float,           # 0-100
        "grade": str,             # A/B/C/D
        "factors": {
            "injury": {"score": float, "weight": 0.4, "detail": str},
            "load_completion": {"score": float, "weight": 0.25, "detail": str},
            "fitness": {"score": float, "weight": 0.25, "detail": str},
            "recovery": {"score": float, "weight": 0.1, "detail": str},
        }
    }
    """
    factors: dict[str, dict[str, Any]] = {}

    # ----- 1. 伤病状态 (40%) -----
    active_injuries = (
        db.query(InjuryLog)
        .filter(InjuryLog.user_id == user_id)
        .filter(InjuryLog.is_resolved == 0)
        .all()
    )
    if not active_injuries:
        injury_score = 100.0
        injury_detail = "无活跃伤病"
    else:
        # 根据最高疼痛等级扣分
        max_pain = max(inj.pain_level for inj in active_injuries)
        # pain_level 0-10 → 分数 100-0
        injury_score = max(0.0, 100.0 - max_pain * 10)
        body_parts = ", ".join(set(inj.body_part for inj in active_injuries))
        injury_detail = (
            f"{len(active_injuries)}处伤病（{body_parts}），最高疼痛{max_pain}/10"
        )

    factors["injury"] = {
        "score": round(injury_score, 1),
        "weight": 0.4,
        "detail": injury_detail,
    }

    # ----- 2. 负荷完成率 (25%) -----
    # 最近 7 天实际跑量
    week_start = target_date - timedelta(days=6)
    recent_activities = (
        db.query(Activity)
        .filter(Activity.user_id == user_id)
        .filter(Activity.activity_date >= week_start)
        .filter(Activity.activity_date <= target_date)
        .all()
    )
    actual_km = sum(
        act.distance_km for act in recent_activities if act.distance_km is not None
    )

    if weekly_mileage_goal_km and weekly_mileage_goal_km > 0:
        completion_ratio = actual_km / weekly_mileage_goal_km
        # 完成率 80%-120% 为满分区间，过高或过低都扣分
        if 0.8 <= completion_ratio <= 1.2:
            load_score = 100.0
        elif completion_ratio < 0.8:
            load_score = max(0.0, completion_ratio / 0.8 * 100)
        else:
            # 超过 120%，每超 10% 扣 10 分
            over = completion_ratio - 1.2
            load_score = max(0.0, 100.0 - over * 100)
        load_detail = f"周跑量 {actual_km:.1f}km / 目标 {weekly_mileage_goal_km:.1f}km（{completion_ratio * 100:.0f}%）"
    else:
        # 无目标时，根据是否有训练给基础分
        load_score = 60.0 if actual_km > 0 else 30.0
        load_detail = f"周跑量 {actual_km:.1f}km（未设定目标）"

    factors["load_completion"] = {
        "score": round(load_score, 1),
        "weight": 0.25,
        "detail": load_detail,
    }

    # ----- 3. 竞技状态 (25%) -----
    acwr_data = calculate_acwr(
        db,
        user_id=user_id,
        target_date=target_date,
        user_max_hr=user_max_hr,
    )
    acwr_val = acwr_data["acwr"]
    acwr_zone = acwr_data["zone"]

    if acwr_zone == "sweet_spot":
        fitness_score = 100.0
    elif acwr_zone == "undertraining":
        fitness_score = 50.0 + acwr_val * 30  # 越接近 0.8 越好
    elif acwr_zone == "caution":
        fitness_score = max(30.0, 100.0 - (acwr_val - 1.3) * 200)
    elif acwr_zone == "danger":
        fitness_score = max(0.0, 30.0 - (acwr_val - 1.5) * 100)
    else:
        fitness_score = 40.0  # 数据不足

    fitness_detail = f"ACWR={acwr_val:.2f}（{acwr_data['zone_label']}）"
    factors["fitness"] = {
        "score": round(fitness_score, 1),
        "weight": 0.25,
        "detail": fitness_detail,
    }

    # ----- 4. 恢复质量 (10%) -----
    recovery_start = target_date - timedelta(days=2)
    recent_summaries = (
        db.query(GarminDailySummary)
        .filter(GarminDailySummary.user_id == user_id)
        .filter(GarminDailySummary.summary_date >= recovery_start)
        .filter(GarminDailySummary.summary_date <= target_date)
        .all()
    )

    sleep_scores = [
        s.sleep_score for s in recent_summaries if s.sleep_score is not None
    ]
    batteries = [s.body_battery for s in recent_summaries if s.body_battery is not None]

    recovery_parts: list[float] = []
    recovery_details: list[str] = []

    if sleep_scores:
        avg_sleep = sum(sleep_scores) / len(sleep_scores)
        # 睡眠评分 60-100 → 0-100
        sleep_normalized = max(0.0, min(100.0, (avg_sleep - 60) / 40 * 100))
        recovery_parts.append(sleep_normalized)
        recovery_details.append(f"睡眠均分{avg_sleep:.0f}")

    if batteries:
        avg_battery = sum(batteries) / len(batteries)
        # 身体电量 0-100 直接映射
        recovery_parts.append(min(100.0, avg_battery))
        recovery_details.append(f"电量均值{avg_battery:.0f}")

    if recovery_parts:
        recovery_score = sum(recovery_parts) / len(recovery_parts)
        recovery_detail = "最近3天：" + "，".join(recovery_details)
    else:
        recovery_score = 50.0
        recovery_detail = "无近期恢复数据"

    factors["recovery"] = {
        "score": round(recovery_score, 1),
        "weight": 0.1,
        "detail": recovery_detail,
    }

    # ----- 汇总 -----
    total = sum(f["score"] * f["weight"] for f in factors.values())
    total = max(0.0, min(100.0, total))

    if total >= 85:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 50:
        grade = "C"
    else:
        grade = "D"

    return {
        "score": round(total, 1),
        "grade": grade,
        "factors": factors,
    }
