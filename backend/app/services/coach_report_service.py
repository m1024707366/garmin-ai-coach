"""教练报告服务：晨间报告 + 晚间复盘 + 周度总结。

整合 ACWR 算法、信心评分、AI 生成个性化建议。
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.db.crud import (
    get_coach_memory,
    get_injury_logs,
    get_recent_weekly_reports,
    upsert_weekly_report,
)
from backend.app.db.models import Activity, GarminDailySummary, WeeklyReport
from backend.app.services.coach_algorithms import calculate_acwr, calculate_confidence_score

logger = logging.getLogger(__name__)


def _seconds_to_pace(seconds_per_km: Optional[float]) -> str:
    """将配速秒数转换为 'M:SS' 格式字符串。"""
    if seconds_per_km is None or seconds_per_km <= 0:
        return "-"
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}"


def _seconds_to_hms(seconds: Optional[float]) -> str:
    """将时长秒数转换为 'H:MM' 格式字符串。"""
    if seconds is None or seconds <= 0:
        return "0:00"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}:{mins:02d}"
    return f"{mins} min"


class CoachReportService:
    """教练报告服务，提供晨间报告、晚间复盘、周度总结功能。"""

    def __init__(self, llm=None) -> None:
        """
        初始化服务。

        Args:
            llm: LLM 服务实例，需要有 chat(prompt: str) -> str 方法。
        """
        self.llm = llm

    def build_morning_report(
        self,
        db: Session,
        user_id: int,
        target_date: date,
    ) -> dict[str, Any]:
        """
        生成晨间报告。

        整合昨晚睡眠、ACWR、信心评分、伤病状态、AI 建议。
        """
        # 1. 获取昨晚睡眠数据
        sleep_data = (
            db.query(GarminDailySummary)
            .filter(GarminDailySummary.user_id == user_id)
            .filter(GarminDailySummary.summary_date == target_date)
            .one_or_none()
        )

        sleep_info: Optional[dict[str, Any]] = None
        if sleep_data:
            # 计算深睡小时数
            deep_sleep_hours = 0.0
            if sleep_data.deep_sleep_seconds:
                deep_sleep_hours = round(sleep_data.deep_sleep_seconds / 3600, 1)
            
            sleep_info = {
                "duration_hours": round(sleep_data.sleep_time_hours, 1) if sleep_data.sleep_time_hours else None,
                "score": sleep_data.sleep_score,
                "deep_sleep_hours": deep_sleep_hours,
                "body_battery": sleep_data.body_battery,
                "resting_hr": sleep_data.resting_heart_rate,
                "hrv_status": sleep_data.hrv_status,
            }

        # 2. ACWR 计算
        acwr_data = calculate_acwr(db, user_id=user_id, target_date=target_date)

        # 3. 获取教练记忆（目标跑量）
        memory = get_coach_memory(db, user_id=user_id)
        weekly_goal = memory.weekly_mileage_goal_km if memory else None

        # 4. 信心评分
        confidence_data = calculate_confidence_score(
            db,
            user_id=user_id,
            target_date=target_date,
            weekly_mileage_goal_km=weekly_goal,
        )

        # 5. 当前活跃伤病
        active_injuries = get_injury_logs(db, user_id=user_id, only_active=True, limit=10)
        injuries_list = [
            {
                "body_part": inj.body_part,
                "pain_level": inj.pain_level,
                "description": inj.description,
            }
            for inj in active_injuries
        ]

        # 6. AI 生成晨间建议
        ai_advice = ""
        if self.llm:
            prompt = self._build_morning_prompt(
                sleep_info=sleep_info,
                acwr=acwr_data,
                confidence=confidence_data,
                injuries=injuries_list,
                target_date=target_date,
                target_race=memory.target_race if memory else None,
                target_race_date=memory.target_race_date if memory else None,
            )
            try:
                ai_advice = self.llm.chat(prompt)
            except Exception as e:
                logger.warning(f"[MorningReport] AI 生成失败: {e}")

        # 构建 training_load（从 acwr_data 提取子集）
        training_load: Optional[dict[str, Any]] = None
        if acwr_data and acwr_data.get("acwr") is not None:
            training_load = {
                "acwr": acwr_data["acwr"],
                "acwr_status": acwr_data.get("zone_label", ""),
                "acute_load": acwr_data.get("atl", 0),
                "chronic_load": acwr_data.get("ctl", 0),
            }

        # 构建 readiness（从 confidence_data 转换）
        readiness: Optional[dict[str, Any]] = None
        if confidence_data and confidence_data.get("score") is not None:
            # 将 0-100 分转为 1-10 分制
            readiness_score = round(confidence_data["score"] / 10, 1)
            factors_dict = confidence_data.get("factors", {})
            factors_list = []
            for fname, fdata in factors_dict.items():
                if isinstance(fdata, dict):
                    factors_list.append({
                        "name": fname,
                        "value": fdata.get("score", 0),
                        "status": fdata.get("detail", ""),
                        "change": None,
                    })
            readiness = {
                "score": readiness_score,
                "verdict": confidence_data.get("grade", ""),
                "factors": factors_list,
            }

        return {
            "target_date": target_date.isoformat(),
            "sleep_summary": sleep_info,
            "training_load": training_load,
            "readiness": readiness,
            "ai_morning_advice": ai_advice,
        }

    def _build_morning_prompt(
        self,
        sleep_info: dict,
        acwr: dict,
        confidence: dict,
        injuries: list,
        target_date: date,
        target_race: Optional[str],
        target_race_date: Optional[date],
    ) -> str:
        """组装晨间报告的提示词。"""
        # 格式化睡眠
        sleep_text = "无睡眠数据"
        if sleep_info and sleep_info.get("duration_hours"):
            sleep_text = f"睡眠 {sleep_info['duration_hours']}h"
            if sleep_info.get("score"):
                sleep_text += f"，睡眠分数 {sleep_info['score']}"
            if sleep_info.get("body_battery"):
                sleep_text += f"，身体电量 {sleep_info['body_battery']}"

        # 格式化伤病
        injury_text = "无"
        if injuries:
            parts = [f"{i['body_part']}({i['pain_level']}/10)" for i in injuries]
            injury_text = "，".join(parts)

        # 格式化目标
        goal_text = ""
        if target_race and target_race_date:
            days_until = (target_race_date - target_date).days
            goal_text = f"\n目标比赛：{target_race}（{target_race_date}，还剩 {days_until} 天）"

        prompt = f"""你是专业跑步教练，请为跑者生成今日晨间训练建议。

=== 今日状态 ===
日期：{target_date}
睡眠：{sleep_text}
静息心率：{sleep_info.get('resting_hr', '-') if sleep_info else '-'} bpm
HRV状态：{sleep_info.get('hrv_status', '-') if sleep_info else '-'}

=== 训练负荷 ===
ACWR：{acwr['acwr']:.2f}（{acwr['zone_label']}）
急性负荷 ATL：{acwr['atl']:.0f}
慢性负荷 CTL：{acwr['ctl']:.0f}
最近7天负荷：{acwr.get('daily_loads_7d', [])}

=== 信心评分 ===
总分：{confidence['score']:.0f}/100（{confidence['grade']}级）
伤病因子：{confidence['factors']['injury']['detail']}
负荷完成因子：{confidence['factors']['load_completion']['detail']}
竞技状态因子：{confidence['factors']['fitness']['detail']}
恢复状态因子：{confidence['factors']['recovery']['detail']}

=== 当前伤病 ===
{injury_text}
{goal_text}

=== 输出要求 ===
1. 总结今日身体状态
2. 根据 ACWR 和信心评分给出今日训练建议（跑休/轻松跑/节奏跑/间歇等）
3. 如果有未愈伤病，给出调整建议
4. 目标比赛倒计时训练提示（如有）
5. 保持简洁，100-200 字
"""
        return prompt

    def build_evening_review(
        self,
        db: Session,
        user_id: int,
        target_date: date,
    ) -> dict[str, Any]:
        """
        生成晚间复盘。

        整合今日跑步活动、健康数据、AI 训练复盘。
        """
        # 1. 获取今日跑步活动
        today_runs = (
            db.query(Activity)
            .filter(Activity.user_id == user_id)
            .filter(Activity.activity_date == target_date)
            .filter(Activity.type.ilike("%run%"))
            .all()
        )

        runs_list: list[dict[str, Any]] = []
        total_km = 0.0
        total_duration = 0.0
        for run in today_runs:
            duration_min = (run.duration_seconds or 0) / 60 if run.duration_seconds else 0
            runs_list.append({
                "type": run.name or "跑步",
                "distance_km": round(run.distance_km, 1) if run.distance_km else 0,
                "duration_min": round(duration_min, 0),
                "avg_pace": _seconds_to_pace(run.average_pace_seconds),
                "avg_hr": run.average_hr,
                "trimp": None,
            })
            total_km += run.distance_km or 0
            total_duration += run.duration_seconds or 0

        # 2. 获取今日健康数据
        health_data = (
            db.query(GarminDailySummary)
            .filter(GarminDailySummary.user_id == user_id)
            .filter(GarminDailySummary.summary_date == target_date)
            .one_or_none()
        )

        recovery_metrics: Optional[dict[str, Any]] = None
        if health_data:
            recovery_metrics = {
                "stress_avg": health_data.average_stress_level,
                "body_battery_end": health_data.body_battery,
                "resting_hr": health_data.resting_heart_rate,
            }

        # 构造 health_info 供 _build_evening_prompt 使用
        health_info: dict[str, Any] = {}
        if health_data:
            health_info = {
                "body_battery": health_data.body_battery,
                "resting_hr": health_data.resting_heart_rate,
                "stress_level": health_data.average_stress_level,
                "hrv_status": health_data.hrv_status,
            }
        # 3. ACWR 计算
        acwr_data = calculate_acwr(db, user_id=user_id, target_date=target_date)

        # 4. AI 晚间复盘
        ai_review = ""
        if self.llm and runs_list:
            prompt = self._build_evening_prompt(
                runs=runs_list,
                total_km=total_km,
                total_duration=total_duration,
                health=health_info,
                acwr=acwr_data,
                target_date=target_date,
            )
            try:
                ai_review = self.llm.chat(prompt)
            except Exception as e:
                logger.warning(f"[EveningReview] AI 生成失败: {e}")

        return {
            "target_date": target_date.isoformat(),
            "today_activities": runs_list,
            "recovery_metrics": recovery_metrics,
            "ai_evening_review": ai_review,
        }

    def _build_evening_prompt(
        self,
        runs: list[dict],
        total_km: float,
        total_duration: float,
        health: dict,
        acwr: dict,
        target_date: date,
    ) -> str:
        """组装晚间复盘的提示词。"""
        runs_text = "\n".join([
            f"- {r['type']}：{r['distance_km']}km，{r['duration_min']}min，配速 {r['avg_pace']}/km，心率 {r.get('avg_hr', '-')}"
            for r in runs
        ])

        prompt = f"""你是专业跑步教练，请复盘跑者今日的训练情况。

=== 今日训练 ===
日期：{target_date}
{runs_text}
总计：{total_km:.1f}km，{_seconds_to_hms(total_duration)}

=== 身体状态 ===
身体电量：{health.get('body_battery', '-')}
静息心率：{health.get('resting_hr', '-')} bpm
压力指数：{health.get('stress_level', '-')}
HRV状态：{health.get('hrv_status', '-')}

=== 当前负荷 ===
ACWR：{acwr['acwr']:.2f}（{acwr['zone_label']}）
ATL：{acwr['atl']:.0f}，CTL：{acwr['ctl']:.0f}

=== 输出要求 ===
1. 简要点评今日训练表现
2. 分析训练强度与身体状态是否匹配
3. 根据当前 ACWR 给出明日训练建议
4. 保持简洁，100-200 字
"""
        return prompt

    def build_weekly_summary(
        self,
        db: Session,
        user_id: int,
        target_date: date,
    ) -> dict[str, Any]:
        """
        生成周度总结。

        整合本周跑步统计、ACWR、信心评分、历史趋势、AI 总结。
        """
        # 1. 计算本周起始日期（周一）
        weekday = target_date.weekday()
        week_start = target_date - timedelta(days=weekday)
        week_end = target_date

        # 2. 获取本周跑步活动
        week_runs = (
            db.query(Activity)
            .filter(Activity.user_id == user_id)
            .filter(Activity.activity_date >= week_start)
            .filter(Activity.activity_date <= week_end)
            .filter(Activity.type.ilike("%run%"))
            .all()
        )

        run_count = len(week_runs)
        total_km = sum((r.distance_km or 0) for r in week_runs)
        total_duration = sum((r.duration_seconds or 0) for r in week_runs)

        avg_pace_seconds = None
        if total_km > 0 and total_duration > 0:
            avg_pace_seconds = total_duration / total_km

        # 3. ACWR
        acwr_data = calculate_acwr(db, user_id=user_id, target_date=target_date)

        # 4. 信心评分
        memory = get_coach_memory(db, user_id=user_id)
        weekly_goal = memory.weekly_mileage_goal_km if memory else None

        confidence_data = calculate_confidence_score(
            db,
            user_id=user_id,
            target_date=target_date,
            weekly_mileage_goal_km=weekly_goal,
        )

        # 5. 历史趋势（过去几周）
        recent_reports = get_recent_weekly_reports(db, user_id=user_id, limit=4)
        trend: list[dict[str, Any]] = []
        for report in recent_reports:
            trend.append({
                "week": f"{report.week_start_date.strftime('%m/%d')}-{report.week_end_date.strftime('%m/%d')}",
                "km": round(report.total_distance_km or 0, 1),
                "run_count": report.run_count or 0,
            })
        # 逆转顺序（从远到近）
        trend.reverse()

        # 6. AI 周度总结
        ai_summary = ""
        if self.llm and run_count > 0:
            prompt = self._build_weekly_prompt(
                week_start=week_start,
                week_end=week_end,
                run_count=run_count,
                total_km=total_km,
                total_duration=total_duration,
                avg_pace=avg_pace_seconds,
                acwr=acwr_data,
                confidence=confidence_data,
                trend=trend,
                weekly_goal=weekly_goal,
            )
            try:
                ai_summary = self.llm.chat(prompt)
            except Exception as e:
                logger.warning(f"[WeeklySummary] AI 生成失败: {e}")

        # 7. 保存到数据库
        try:
            upsert_weekly_report(
                db,
                user_id=user_id,
                week_start_date=week_start,
                week_end_date=week_end,
                total_distance_km=total_km,
                total_duration_seconds=total_duration,
                run_count=run_count,
                avg_pace_seconds=avg_pace_seconds,
                acwr=acwr_data.get("acwr"),
                confidence_score=confidence_data.get("score"),
                ai_summary=ai_summary,
            )
            db.commit()
            logger.info(f"[WeeklySummary] 周报已保存: {week_start} - {week_end}")
        except Exception as e:
            logger.warning(f"[WeeklySummary] 保存失败: {e}")
            db.rollback()

        # 构建 weekly_stats
        weekly_stats: Optional[dict[str, Any]] = {
            "total_distance_km": round(total_km, 1),
            "run_count": run_count,
            "total_duration_min": round(total_duration / 60, 0) if total_duration else 0,
            "avg_pace": _seconds_to_pace(avg_pace_seconds),
            "avg_hr": None,
        } if run_count > 0 else None

        # 构建 load_trend（从 acwr_data 提取）
        load_trend: Optional[dict[str, Any]] = None
        if acwr_data and acwr_data.get("acwr") is not None:
            load_trend = {
                "acwr": acwr_data["acwr"],
                "acwr_status": acwr_data.get("zone_label", ""),
                "weekly_trimp": None,
            }

        # 构建 confidence_score（从 confidence_data 转换）
        confidence_score_out: Optional[dict[str, Any]] = None
        if confidence_data and confidence_data.get("score") is not None:
            factors_dict = confidence_data.get("factors", {})
            factors_list = []
            for fname, fdata in factors_dict.items():
                if isinstance(fdata, dict):
                    factors_list.append({
                        "name": fname,
                        "score": fdata.get("score", 0),
                        "detail": fdata.get("detail", ""),
                    })
            confidence_score_out = {
                "score": confidence_data["score"],
                "label": confidence_data.get("grade", ""),
                "factors": factors_list,
            }

        return {
            "target_date": target_date.isoformat(),
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "weekly_stats": weekly_stats,
            "load_trend": load_trend,
            "confidence_score": confidence_score_out,
            "ai_weekly_summary": ai_summary,
        }

    def _build_weekly_prompt(
        self,
        week_start: date,
        week_end: date,
        run_count: int,
        total_km: float,
        total_duration: float,
        avg_pace_seconds: Optional[float],
        acwr: dict,
        confidence: dict,
        trend: list[dict],
        weekly_goal: Optional[float],
    ) -> str:
        """组装周度总结的提示词。"""
        # 趋势格式化
        trend_text = "\n".join([f"- {t['week']}: {t['km']}km（{t['run_count']}次）" for t in trend]) or "无历史数据"

        goal_text = ""
        if weekly_goal:
            goal_pct = total_km / weekly_goal * 100
            goal_text = f"\n周跑量目标：{weekly_goal}km（当前 {goal_pct:.0f}%）"

        prompt = f"""你是专业跑步教练，请为跑者生成本周训练总结。

=== 本周概况 ===
周期：{week_start} - {week_end}
跑步次数：{run_count} 次
总跑量：{total_km:.1f} km
总时长：{_seconds_to_hms(total_duration)}
平均配速：{_seconds_to_pace(avg_pace_seconds)}/km{goal_text}

=== 负荷状态 ===
ACWR：{acwr['acwr']:.2f}（{acwr['zone_label']}）
ATL：{acwr['atl']:.0f}，CTL：{acwr['ctl']:.0f}

=== 信心评分 ===
总分：{confidence['score']}/100（{confidence['grade']}级）
伤病：{confidence['factors']['injury']['detail']}
负荷完成：{confidence['factors']['load_completion']['detail']}
竞技状态：{confidence['factors']['fitness']['detail']}
恢复状态：{confidence['factors']['recovery']['detail']}

=== 历史趋势 ===
{trend_text}

=== 输出要求 ===
1. 总结本周训练表现（亮点与不足）
2. 根据 ACWR 和信心评分分析当前训练状态
3. 为下周训练给出具体建议（休整/渐进/维持/减量）
4. 保持简洁，150-300 字
"""
        return prompt
