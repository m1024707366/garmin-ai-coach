from __future__ import annotations

import logging
import time
from datetime import date as date_type, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.db.crud import (
    get_activities_by_date,
    get_cached_analysis,
    get_daily_summary_by_date,
    get_garmin_credential,
    get_or_create_user,
    get_training_plans_in_range,
    get_user_profile,
    save_analysis,
    upsert_activities,
    upsert_daily_summary,
    upsert_training_plans,
    upsert_user_profile,
)
from backend.app.services.data_processor import DataProcessor
from backend.app.services.llm_factory import get_llm_service

# 仅在非mock模式下导入GarminClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.config import settings

GarminClient = None
if not settings.USE_MOCK_MODE:
    from backend.app.services.garmin_client import GarminClient
from backend.app.utils.crypto import decrypt_text


logger = logging.getLogger(__name__)


class ReportService:
    def __init__(
        self,
        *,
        processor: Optional[DataProcessor] = None,
        llm=None,
    ) -> None:
        self.processor = processor or DataProcessor()
        self.gemini = llm or get_llm_service()

    def build_daily_analysis(
        self,
        *,
        wechat_user_id: Optional[int],
        analysis_date: str,
        force_refresh: bool,
        db: Optional[Session],
    ) -> dict[str, Any]:
        request_start_time = time.time()
        analysis_date_obj = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        credential = None
        if db is not None and wechat_user_id is not None:
            credential = get_garmin_credential(db, wechat_user_id=wechat_user_id)

        if wechat_user_id is not None:
            if db is None:
                raise HTTPException(status_code=500, detail="数据库不可用")
            if not settings.USE_MOCK_MODE and credential is None:
                raise HTTPException(status_code=403, detail="请先绑定 Garmin 账号")

        garmin_identity_email: Optional[str] = None
        if credential is not None and credential.garmin_email:
            garmin_identity_email = credential.garmin_email
        elif wechat_user_id is None:
            garmin_identity_email = settings.GARMIN_EMAIL

        db_user_id: Optional[int] = None
        cache_hours = max(int(settings.ANALYSIS_CACHE_HOURS), 0)
        if db is not None and garmin_identity_email:
            try:
                user = get_or_create_user(db, garmin_email=garmin_identity_email)
                db_user_id = user.id
                if not force_refresh:
                    cached = get_cached_analysis(db, user_id=db_user_id, analysis_date=analysis_date_obj)
                    if cached is not None:
                        is_fresh = (
                            cache_hours > 0
                            and cached.generated_at is not None
                            and (datetime.utcnow() - cached.generated_at) <= timedelta(hours=cache_hours)
                        )
                        if is_fresh:
                            return {
                                "date": analysis_date,
                                "raw_data_summary": cached.raw_data_summary_md,
                                "ai_advice": cached.ai_advice_md,
                                "charts": cached.charts_json,
                            }
            except Exception as e:
                logger.warning(f"[DB] Cache lookup failed, continuing without cache: {e}")
                db_user_id = None

        raw_health: Optional[Dict[str, Any]] = None
        raw_plan: List[Dict[str, Any]] = []
        raw_activities_new: List[Dict[str, Any]] = []
        data_source = "none"

        if not force_refresh and db is not None and db_user_id is not None:
            try:
                summary_row = get_daily_summary_by_date(db, user_id=db_user_id, summary_date=analysis_date_obj)
                activity_rows = get_activities_by_date(db, user_id=db_user_id, activity_date=analysis_date_obj)
                plan_rows = get_training_plans_in_range(
                    db,
                    user_id=db_user_id,
                    start_date=analysis_date_obj,
                    end_date=analysis_date_obj + timedelta(days=2),
                )

                if summary_row is not None:
                    raw_health = summary_row.raw_json
                for activity_row in activity_rows:
                    raw_activities_new.append(activity_row.raw_json)
                for plan_row in plan_rows:
                    raw_plan.append(plan_row.raw_json)

                if raw_health or raw_activities_new or raw_plan:
                    data_source = "db"
            except Exception as e:
                logger.warning(f"[DB] Failed to load raw data, fallback to Garmin: {e}")

        if data_source != "db":
            if settings.USE_MOCK_MODE:
                # 直接实现mock数据获取，避免导入GarminClient
                from datetime import datetime, timedelta
                import json
                import os
                
                # 尝试从mock文件读取数据
                def get_mock_data(target_date):
                    # 首先尝试从 backend/app/data/mock_garmin.json 读取
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    mock_file = os.path.join(current_dir, "..", "data", "mock_garmin.json")
                    
                    # 如果文件不存在，尝试相对路径
                    if not os.path.exists(mock_file):
                        mock_file = os.path.join(current_dir, "..", "..", "..", "backend", "app", "data", "mock_garmin.json")
                    
                    mock_data = None
                    target_day = None
                    
                    # 尝试读取 mock_garmin.json
                    if os.path.exists(mock_file):
                        try:
                            with open(mock_file, "r", encoding="utf-8") as f:
                                mock_data = json.load(f)
                            # 在 days 数组中查找匹配的日期
                            days = mock_data.get("days", [])
                            for day in days:
                                if day.get("date") == target_date:
                                    target_day = day
                                    break
                        except Exception as e:
                            pass
                    
                    if not target_day:
                        # 如果找不到指定日期，返回默认数据
                        return None, None, []
                    
                    # 提取活动数据（第一个活动）
                    activity = None
                    activities = target_day.get("activities", [])
                    if activities and len(activities) > 0:
                        activity = activities[0]  # 使用第一个活动
                    
                    # 构造健康数据
                    health = {
                        "date": target_date,
                        "sleep_time_seconds": 28800,  # 8小时
                        "sleep_time_hours": 8.0,
                        "sleep_score": 85,
                        "deep_sleep_seconds": 7200,  # 2小时
                        "deep_sleep_hh_mm": "2:00",
                        "rem_sleep_seconds": 3600,  # 1小时
                        "rem_sleep_hh_mm": "1:00",
                        "light_sleep_seconds": 14400,  # 4小时
                        "light_sleep_hh_mm": "4:00",
                        "awake_sleep_seconds": 3600,  # 1小时
                        "awake_sleep_hh_mm": "1:00",
                        "resting_heart_rate": 65,
                        "body_battery": 60,
                        "average_stress_level": 35,
                        "stress_qualifier": "BALANCED"
                    }
                    
                    # 训练计划（返回简单的模拟计划）
                    plan = [
                        {
                            "date": (datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                            "workoutName": "轻松跑 40分钟",
                            "description": "恢复性训练",
                        },
                        {
                            "date": (datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d"),
                            "workoutName": "休息日",
                            "description": "",
                        },
                    ]
                    
                    return activity, health, plan
                
                mock_activity, mock_health, mock_plan = get_mock_data(analysis_date)
                raw_health = mock_health
                raw_plan = mock_plan or []
                if mock_activity:
                    raw_activities_new = [mock_activity]
                data_source = "mock"
            else:
                if credential is None:
                    raise HTTPException(status_code=403, detail="请先绑定 Garmin 账号")

                # 确保在非mock模式下才导入和使用GarminService和GarminClient
                from backend.app.services.garmin_client import GarminClient
                from src.services.garmin_service import GarminService

                garmin_password = decrypt_text(credential.garmin_password)
                garmin_client = GarminClient(
                    email=credential.garmin_email,
                    password=garmin_password,
                    is_cn=bool(credential.is_cn),
                )
                garmin_service = GarminService(credential.garmin_email, garmin_password)

                try:
                    daily_data = garmin_service.get_daily_data(analysis_date)
                    activities = daily_data.get("activities") or []
                    if activities:
                        raw_activities_new = [a for a in activities if isinstance(a, dict)]
                except Exception:
                    raw_activities_new = []

                try:
                    health_data = garmin_client.get_health_stats(analysis_date)
                    if health_data:
                        raw_health = health_data
                except Exception:
                    raw_health = None

                try:
                    plan_data = garmin_client.get_training_plan(analysis_date, days=3)
                    if plan_data:
                        raw_plan = plan_data
                except Exception:
                    raw_plan = []

                data_source = "garmin"

                # ====== 调试日志：检查获取到的数据 ======
                logger.info(f"[DEBUG] 获取到活动数量: {len(raw_activities_new)}")
                if raw_activities_new:
                    logger.info(f"[DEBUG] 活动样本: {raw_activities_new[0]}")
                logger.info(f"[DEBUG] db_user_id: {db_user_id}, data_source: {data_source}")
                # ====== 调试日志结束 ======

        activity_md, health_md, plan_md, converted_activities = _build_context_from_raw(
            processor=self.processor,
            raw_activities_new=raw_activities_new,
            raw_health=raw_health,
            raw_plan=raw_plan,
        )

        # ====== 调试日志：检查保存条件 ======
        logger.info(f"[DEBUG] 保存条件检查: db={db is not None}, db_user_id={db_user_id}, data_source={data_source}")
        logger.info(f"[DEBUG] raw_activities_new 数量: {len(raw_activities_new) if raw_activities_new else 0}")
        # ====== 调试日志结束 ======

        if db is not None and db_user_id is not None and data_source in ("garmin", "mock"):
            try:
                if raw_health:
                    upsert_daily_summary(db, user_id=db_user_id, health=raw_health, summary_date=analysis_date_obj)
                if raw_activities_new:
                    saved_count = upsert_activities(db, user_id=db_user_id, activities=raw_activities_new, fallback_date=analysis_date_obj)
                    logger.info(f"[DEBUG] 成功保存活动数量: {len(saved_count) if saved_count else 0}")
                if raw_plan:
                    upsert_training_plans(db, user_id=db_user_id, plans=raw_plan)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"[DB] Failed to persist raw data: {e}")

        daily_context = self.processor.assemble_daily_report(
            activity_md,
            health_md,
            plan_md,
            activity_date=analysis_date,
        )

        if not daily_context or daily_context.strip() == "暂无数据":
            empty_ai_advice = "## 📊 分析结果\n\n**提示**: 今天还没有运动数据或健康数据。请确保 Garmin 设备已同步数据。"
            if db is not None and db_user_id is not None:
                try:
                    save_analysis(
                        db,
                        user_id=db_user_id,
                        analysis_date=analysis_date_obj,
                        raw_data_summary_md="暂无数据",
                        ai_advice_md=empty_ai_advice,
                        charts_json=None,
                        model_name=getattr(self.gemini, "model_name", None),
                        status="no_data",
                        error_message=None,
                    )
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning(f"[DB] Failed to persist empty analysis: {e}")

            return {
                "date": analysis_date,
                "raw_data_summary": "暂无数据",
                "ai_advice": empty_ai_advice,
                "charts": None,
            }

        analysis_status = "success"
        analysis_error: Optional[str] = None
        try:
            ai_advice = self.gemini.analyze_training(daily_context)
        except Exception as e:
            analysis_status = "error"
            analysis_error = str(e)
            ai_advice = f"""## 📊 分析结果

**抱歉，AI 分析暂时不可用**

错误信息: {str(e)}

**建议**: 请稍后重试，或检查网络连接。
"""

        charts_data: Optional[Dict[str, List]] = None
        if converted_activities:
            first_activity = converted_activities[0]
            try:
                charts_data = self.processor.extract_chart_data(first_activity)
            except Exception as e:
                logger.warning(f"[API] 提取图表数据失败: {str(e)}")
                charts_data = None

        if db is not None and db_user_id is not None:
            try:
                save_analysis(
                    db,
                    user_id=db_user_id,
                    analysis_date=analysis_date_obj,
                    raw_data_summary_md=daily_context,
                    ai_advice_md=ai_advice,
                    charts_json=charts_data,
                    model_name=getattr(self.gemini, "model_name", None),
                    status=analysis_status,
                    error_message=analysis_error,
                )
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"[DB] Failed to persist analysis: {e}")

        total_elapsed = time.time() - request_start_time
        logger.info(f"[API] 请求处理完毕，准备返回，总耗时 {total_elapsed:.2f}s")
        return {
            "date": analysis_date,
            "raw_data_summary": daily_context,
            "ai_advice": ai_advice,
            "charts": charts_data,
        }

    def sync_recent_history(
        self,
        *,
        wechat_user_id: int,
        days: int,
        db: Session,
    ) -> dict[str, int]:
        if days <= 0:
            return {
                "days_requested": 0,
                "days_processed": 0,
                "days_with_data": 0,
                "days_failed": 0,
                "activities_synced": 0,
                "health_days_synced": 0,
            }

        credential = get_garmin_credential(db, wechat_user_id=wechat_user_id)
        if credential is None:
            raise RuntimeError("Garmin 未绑定，无法执行历史回填")

        garmin_password = decrypt_text(credential.garmin_password)
        user = get_or_create_user(db, garmin_email=credential.garmin_email)
        db_user_id = user.id

        # 确保在非mock模式下才导入和使用GarminService和GarminClient
        from backend.app.services.garmin_client import GarminClient
        from src.services.garmin_service import GarminService

        garmin_client = GarminClient(
            email=credential.garmin_email,
            password=garmin_password,
            is_cn=bool(credential.is_cn),
        )
        garmin_service = GarminService(credential.garmin_email, garmin_password)

        summary = {
            "days_requested": int(days),
            "days_processed": 0,
            "days_with_data": 0,
            "days_failed": 0,
            "activities_synced": 0,
            "health_days_synced": 0,
        }

        today = datetime.now().date()
        for offset in range(days):
            target_date = today - timedelta(days=offset)
            target_date_str = target_date.isoformat()
            summary["days_processed"] += 1

            raw_activities: List[Dict[str, Any]] = []
            raw_health: Optional[Dict[str, Any]] = None

            try:
                try:
                    daily_data = garmin_service.get_daily_data(target_date_str)
                    activities = daily_data.get("activities") or []
                    if activities:
                        raw_activities = [a for a in activities if isinstance(a, dict)]
                except Exception:
                    raw_activities = []

                try:
                    health_data = garmin_client.get_health_stats(target_date_str)
                    if health_data:
                        raw_health = health_data
                except Exception:
                    raw_health = None

                day_has_data = False
                if raw_health:
                    upsert_daily_summary(db, user_id=db_user_id, health=raw_health, summary_date=target_date)
                    summary["health_days_synced"] += 1
                    day_has_data = True

                if raw_activities:
                    saved_activities = upsert_activities(
                        db,
                        user_id=db_user_id,
                        activities=raw_activities,
                        fallback_date=target_date,
                    )
                    summary["activities_synced"] += len(saved_activities)
                    day_has_data = True

                if day_has_data:
                    summary["days_with_data"] += 1

                db.commit()
            except Exception as e:
                db.rollback()
                summary["days_failed"] += 1
                logger.warning(f"[Backfill] day sync failed: date={target_date_str}, error={e}")

        return summary


def _convert_activity_for_processor(activity: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(activity, dict) or "metrics" not in activity:
        return activity

    metrics = activity.get("metrics") if isinstance(activity.get("metrics"), dict) else {}
    distance_km = metrics.get("distance_km")
    duration_s = metrics.get("duration_seconds")
    distance_m = float(distance_km) * 1000.0 if isinstance(distance_km, (int, float)) else None

    avg_speed_mps = None
    if isinstance(distance_m, (int, float)) and isinstance(duration_s, (int, float)) and float(duration_s) > 0:
        avg_speed_mps = float(distance_m) / float(duration_s)

    converted: Dict[str, Any] = {
        "type": activity.get("type"),
        "activityName": activity.get("name"),
        "distance": distance_m,
        "duration": duration_s,
        "averageHR": metrics.get("average_hr"),
        "maxHR": metrics.get("max_hr"),
        "averageSpeed": avg_speed_mps,
        "startTimeLocal": activity.get("start_time_local") or activity.get("startTimeLocal") or "",
    }

    laps = activity.get("laps") if isinstance(activity.get("laps"), list) else []
    splits: List[Dict[str, Any]] = []
    for lap in laps:
        if not isinstance(lap, dict):
            continue
        lap_distance_km = lap.get("distance_km")
        lap_duration_s = lap.get("duration_seconds")
        lap_distance_m = float(lap_distance_km) * 1000.0 if isinstance(lap_distance_km, (int, float)) else None

        lap_speed_mps = None
        if (
            isinstance(lap_distance_m, (int, float))
            and isinstance(lap_duration_s, (int, float))
            and float(lap_duration_s) > 0
        ):
            lap_speed_mps = float(lap_distance_m) / float(lap_duration_s)

        splits.append(
            {
                "lapIndex": lap.get("lap_index"),
                "distance": lap_distance_m,
                "duration": lap_duration_s,
                "averageHR": lap.get("average_hr"),
                "maxHR": lap.get("max_hr"),
                "strideLength": lap.get("stride_length_cm"),
                "groundContactTime": lap.get("ground_contact_time_ms"),
                "verticalOscillation": lap.get("vertical_oscillation_cm"),
                "verticalRatio": lap.get("vertical_ratio_percent"),
                "averageRunCadence": lap.get("cadence"),
                "averageSpeed": lap_speed_mps,
            }
        )

    converted["splits"] = splits
    return converted


def _build_context_from_raw(
    processor: DataProcessor,
    raw_activities_new: List[Dict[str, Any]],
    raw_health: Optional[Dict[str, Any]],
    raw_plan: List[Dict[str, Any]],
) -> tuple[Optional[str], Optional[str], Optional[str], List[Dict[str, Any]]]:
    converted_activities = [_convert_activity_for_processor(a) for a in raw_activities_new]

    activity_md: Optional[str] = None
    if converted_activities:
        simplified = [processor.simplify_activity(a) for a in converted_activities]
        activity_md = processor.format_for_llm(simplified)

    health_md: Optional[str] = None
    if raw_health:
        health_md = processor.format_health_summary(raw_health)

    plan_md: Optional[str] = None
    if raw_plan:
        plan_md = processor.format_future_plan(raw_plan)

    return activity_md, health_md, plan_md, converted_activities
