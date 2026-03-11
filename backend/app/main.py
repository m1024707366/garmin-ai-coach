"""
GarminCoach - FastAPI Application
提供 RESTful API 接口，整合 Garmin 数据和 AI 教练分析。
"""
import logging
import sys
import os
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置全局 Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ProjectRunner")

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy.orm import Session


from backend.app.services.data_processor import DataProcessor
from backend.app.services.llm_factory import get_llm_service
from backend.app.services.home_summary_service import HomeSummaryService
from backend.app.services.coach_report_service import CoachReportService

# 仅在非mock模式下导入ReportService和Garmin相关模块
USE_MOCK_MODE = True  # 启用mock模式，避免garth库的兼容性问题
GarminClient = None
start_scheduler = None
GarminService = None
ReportService = None

if not USE_MOCK_MODE:
    from backend.app.services.report_service import ReportService
    from backend.app.services.garmin_client import GarminClient
    from backend.app.jobs.scheduler import start_scheduler
    from src.services.garmin_service import GarminService
else:
    # 在mock模式下，使用一个简单的ReportService替代品
    class ReportService:
        def __init__(self, processor=None, llm=None):
            self.processor = processor
            self.gemini = llm
        def build_daily_analysis(self, wechat_user_id, analysis_date, force_refresh, db):
            return {
                "date": analysis_date,
                "raw_data_summary": "## 📊 模拟数据\n\n**今天的跑步数据**\n- 距离: 5.0 km\n- 时间: 25:00\n- 配速: 5:00 / km\n- 平均心率: 140 bpm\n\n**睡眠数据**\n- 睡眠时长: 8.0 小时\n- 睡眠质量: 良好\n",
                "ai_advice": "## 📊 分析结果\n\n**今天的训练表现良好**\n- 配速稳定，心率控制在合理范围内\n- 建议明天进行轻度恢复训练\n- 保持良好的睡眠习惯\n",
                "charts": None
            }

from backend.app.db.crud import get_home_summary, upsert_home_summary, get_garmin_credential, get_coach_memory, upsert_coach_memory, get_injury_logs, create_injury_log, update_injury_log
from backend.app.db.models import WechatUser, User
from backend.app.db.session import get_db_optional, init_db
from src.core.config import settings


# 初始化 FastAPI 应用
app = FastAPI(
    title="GarminCoach API",
    description="基于 Garmin 数据和 AI 的跑步教练分析服务",
    version="1.0.0",
)



_scheduler = None


@app.on_event("startup")
def _startup() -> None:
    try:
        init_db()
    except Exception as e:
        logger.error(f"[DB] Startup init failed: {e}")

    global _scheduler
    if settings.ENABLE_GARMIN_POLLING:
        try:
            _scheduler = start_scheduler()
        except Exception as e:
            logger.error(f"[Scheduler] Startup failed: {e}")


@app.on_event("shutdown")
def _shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"[Scheduler] Shutdown failed: {e}")
        finally:
            _scheduler = None

# CORS 中间件配置
# 生产环境应该配置具体的域名，而不是使用通配符
ALLOWED_ORIGINS = ["*"]  # 开发环境使用通配符
# 生产环境示例：
# ALLOWED_ORIGINS = ["https://your-domain.com", "https://www.your-domain.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 响应模型
class DailyAnalysisResponse(BaseModel):
    """每日分析响应模型"""
    date: str
    raw_data_summary: str  # 清洗后的 Markdown 文本，用于前端展示数据概览
    ai_advice: str  # Gemini 的建议
    charts: Optional[Dict[str, List]] = None  # 图表数据（labels, paces, heart_rates, cadences）


class HomeSummaryResponse(BaseModel):
    latest_run: Optional[Dict[str, Any]] = None
    week_stats: Optional[Dict[str, Any]] = None
    month_stats: Optional[Dict[str, Any]] = None
    ai_brief: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None


class PeriodAnalysisResponse(BaseModel):
    period: str  # "week" or "month"
    start_date: str
    end_date: str
    run_count: int
    total_distance_km: float
    avg_speed_kmh: Optional[float] = None
    sleep_days: int
    avg_sleep_hours: Optional[float] = None
    ai_analysis: Optional[str] = None




# 依赖注入：初始化服务实例
def get_garmin_client() -> Optional[GarminClient]:
    """
    获取 GarminClient 实例（依赖注入）。
    
    注意：每次请求都会创建新实例并登录，如果频繁调用可能触发 Garmin 限流。
    生产环境建议使用连接池或缓存机制。
    
    Mock Mode: 如果 USE_MOCK_MODE=True，返回 None（不需要真实的客户端）。
    """
    if USE_MOCK_MODE:
        # Mock Mode: 不需要真实的客户端，返回 None
        return None
    else:
        try:
            return GarminClient()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Garmin 登录失败: {str(e)}。请检查 .env 文件中的账号密码是否正确。"
            )


def get_garmin_service() -> Optional[GarminService]:
    """
    获取 GarminService 实例（依赖注入）。
    
    用于获取活动数据。
    
    Mock Mode: 如果 USE_MOCK_MODE=True，返回 None（不需要真实服务）。
    """
    if USE_MOCK_MODE:
        return None
    else:
        try:
            return GarminService(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Garmin 服务初始化失败: {str(e)}"
            )


def get_data_processor() -> DataProcessor:
    """获取 DataProcessor 实例（依赖注入）。"""
    return DataProcessor()


_llm_singleton = None


def get_llm():
    """获取 LLM 服务实例（依赖注入）。根据 LLM_PROVIDER 配置自动切换 DeepSeek/Gemini。"""
    global _llm_singleton
    if _llm_singleton is None:
        _llm_singleton = get_llm_service()
    return _llm_singleton

def get_report_service(
    processor: DataProcessor = Depends(get_data_processor),
    llm=Depends(get_llm),
) -> ReportService:
    return ReportService(processor=processor, llm=llm)


def get_home_summary_service(
    llm=Depends(get_llm),
) -> HomeSummaryService:
    return HomeSummaryService(llm=llm)

def get_coach_report_service(
    llm=Depends(get_llm),
) -> CoachReportService:
    return CoachReportService(llm=llm)


def _convert_activity_for_processor(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Convert the new parsed activity format into DataProcessor's expected format."""

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


def _activity_to_new_format_from_db(activity: Any) -> Dict[str, Any]:
    metrics = {
        "distance_km": activity.distance_km,
        "duration_seconds": activity.duration_seconds,
        "average_hr": activity.average_hr,
        "max_hr": activity.max_hr,
        "calories": activity.calories,
        "average_cadence": activity.average_cadence,
        "average_stride_length_cm": activity.average_stride_length_cm,
        "average_ground_contact_time_ms": activity.average_ground_contact_time_ms,
        "average_vertical_oscillation_cm": activity.average_vertical_oscillation_cm,
        "average_vertical_ratio_percent": activity.average_vertical_ratio_percent,
    }
    laps = []
    for lap in activity.laps or []:
        laps.append(
            {
                "lap_index": lap.lap_index,
                "distance_km": lap.distance_km,
                "duration_seconds": lap.duration_seconds,
                "average_hr": lap.average_hr,
                "max_hr": lap.max_hr,
                "cadence": lap.cadence,
                "stride_length_cm": lap.stride_length_cm,
                "ground_contact_time_ms": lap.ground_contact_time_ms,
                "vertical_oscillation_cm": lap.vertical_oscillation_cm,
                "vertical_ratio_percent": lap.vertical_ratio_percent,
            }
        )

    start_time_local = ""
    if activity.start_time_local is not None:
        start_time_local = activity.start_time_local.isoformat()

    return {
        "type": activity.type,
        "name": activity.name,
        "activity_id": activity.garmin_activity_id,
        "start_time_local": start_time_local,
        "metrics": metrics,
        "laps": laps,
    }


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


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Welcome to GarminCoach API",
        "version": "1.0.0",
        "endpoints": {
            "daily_analysis": "/api/coach/daily-analysis",
            "health": "/health",
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/coach/home-summary", response_model=HomeSummaryResponse)
async def get_home_summary_endpoint(
    db: Optional[Session] = Depends(get_db_optional),
    home_summary_service: HomeSummaryService = Depends(get_home_summary_service),
):
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    # 暂时使用固定的用户 ID，实际生产环境需要实现用户认证
    wechat_user_id = 1
    cached = get_home_summary(db, wechat_user_id=wechat_user_id)
    try:
        summary = home_summary_service.build_summary(
            db=db,
            wechat_user_id=wechat_user_id,
            include_ai_brief=False,
        )

        upsert_home_summary(
            db,
            wechat_user_id=wechat_user_id,
            latest_run_json=summary.get("latest_run"),
            week_stats_json=summary.get("week_stats"),
            month_stats_json=summary.get("month_stats"),
            ai_brief_json=None,
        )
        db.commit()

        return HomeSummaryResponse(
            latest_run=summary.get("latest_run"),
            week_stats=summary.get("week_stats"),
            month_stats=summary.get("month_stats"),
            ai_brief=None,
            updated_at=summary.get("updated_at"),
        )
    except Exception as e:
        db.rollback()
        logger.warning(f"[HomeSummary] rebuild failed, fallback to cache: {e}")
        if cached:
            return HomeSummaryResponse(
                latest_run=cached.latest_run_json,
                week_stats=cached.week_stats_json,
                month_stats=cached.month_stats_json,
                ai_brief=None,
                updated_at=cached.updated_at.isoformat() if cached.updated_at else None,
            )
        raise HTTPException(status_code=500, detail="首页摘要生成失败")


@app.get("/api/coach/period-analysis", response_model=PeriodAnalysisResponse)
async def get_period_analysis(
    period: str,  # "week" or "month"
    db: Optional[Session] = Depends(get_db_optional),
    llm=Depends(get_llm),
):
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    from datetime import date, timedelta
    today = date.today()

    if period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "month":
        start_date = today.replace(day=1)
        end_date = today
    else:
        raise HTTPException(status_code=400, detail="无效的周期类型")

    # 获取 Garmin 凭证和 User（crud/models 已在顶部导入）
    from backend.app.db.models import Activity, GarminDailySummary
    from sqlalchemy import func

    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")

    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 查询跑步数据
    runs = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.activity_date >= start_date,
        Activity.activity_date <= end_date,
        Activity.type.ilike("%run%"),
    ).all()

    run_count = len(runs)
    total_distance = sum((r.distance_km or 0) for r in runs)
    total_duration = sum((r.duration_seconds or 0) for r in runs)
    avg_speed = None
    if run_count >= 2 and total_distance >= 5 and total_duration > 0:
        avg_speed = round(total_distance / (total_duration / 3600.0), 1)

    # 查询睡眠数据
    sleep_records = db.query(GarminDailySummary).filter(
        GarminDailySummary.user_id == user.id,
        GarminDailySummary.summary_date >= start_date,
        GarminDailySummary.summary_date <= end_date,
    ).all()

    sleep_days = 0
    total_sleep_hours = 0.0
    for rec in sleep_records:
        if rec.sleep_time_hours is not None:
            sleep_days += 1
            total_sleep_hours += rec.sleep_time_hours
        elif rec.sleep_time_seconds is not None:
            sleep_days += 1
            total_sleep_hours += rec.sleep_time_seconds / 3600.0

    avg_sleep_hours = round(total_sleep_hours / sleep_days, 1) if sleep_days > 0 else None

    # ====== 获取历史趋势数据 ======
    # 查询上一周期（用于对比）
    days_in_period = (end_date - start_date).days + 1
    prev_start_date = start_date - timedelta(days=days_in_period)
    prev_end_date = start_date - timedelta(days=1)
    
    prev_runs = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.activity_date >= prev_start_date,
        Activity.activity_date <= prev_end_date,
        Activity.type.ilike("%run%"),
    ).all()
    
    prev_run_count = len(prev_runs)
    prev_total_distance = sum((r.distance_km or 0) for r in prev_runs)
    
    # 计算趋势
    distance_trend = "增长" if total_distance > prev_total_distance else ("下降" if total_distance < prev_total_distance else "持平")
    frequency_trend = "增加" if run_count > prev_run_count else ("减少" if run_count < prev_run_count else "持平")

    # 查询最近 30 天的活动（用于分析训练频率）
    recent_start_date = today - timedelta(days=30)
    recent_runs = db.query(Activity).filter(
        Activity.user_id == user.id,
        Activity.activity_date >= recent_start_date,
        Activity.activity_date <= today,
        Activity.type.ilike("%run%"),
    ).all()
    
    recent_run_count = len(recent_runs)
    recent_total_distance = sum((r.distance_km or 0) for r in recent_runs)

    # ====== AI 分析（含训练建议）======
    ai_analysis = None

    # AI 分析
    ai_analysis = None
    # 周至少 1 次跑步 + 1 天睡眠，月至少 3 次跑步 + 3 天睡眠
    min_run = 1 if period == "week" else 3
    min_sleep = 1 if period == "week" else 3

    if run_count >= min_run and sleep_days >= min_sleep:
        try:
            prompt = (
                f"作为跑步教练，请分析以下数据并给出简要建议（不超过50字）：\n"
                f"周期：{period}\n"
                f"日期：{start_date} 至 {end_date}\n"
                f"跑步次数：{run_count}\n"
                f"总跑量：{total_distance:.1f}km\n"
                f"平均速度：{avg_speed or '-'} km/h\n"
                f"睡眠天数：{sleep_days}\n"
                f"平均睡眠：{avg_sleep_hours or '-'} 小时"
            )
            ai_analysis = llm.analyze_training(prompt)
        except Exception as e:
            logger.warning(f"[PeriodAnalysis] AI analysis failed: {e}")

    return PeriodAnalysisResponse(
        period=period,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        run_count=run_count,
        total_distance_km=round(total_distance, 1),
        avg_speed_kmh=avg_speed,
        sleep_days=sleep_days,
        avg_sleep_hours=avg_sleep_hours,
        ai_analysis=ai_analysis,
    )


@app.get("/api/coach/daily-analysis", response_model=DailyAnalysisResponse)
async def get_daily_analysis(
    target_date: Optional[str] = None,
    force_refresh: bool = False,
    db: Optional[Session] = Depends(get_db_optional),
    report_service: ReportService = Depends(get_report_service),
):
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")
    wechat_user_id = 1
    """
    获取每日训练分析和 AI 教练建议。
    
    流程：
    1. 获取数据：今日跑步活动、昨晚睡眠、今日身体电量/HRV、未来3天训练计划
    2. 清洗数据：使用 DataProcessor 将原始数据转化为 Markdown 格式
    3. AI 分析：将清洗后的数据发送给 GeminiService
    4. 返回结果：包含原始数据摘要和 AI 建议
    
    Args:
        target_date: 目标日期，格式 "YYYY-MM-DD"。如果不提供，使用今天。
        garmin_client: GarminClient 实例（依赖注入）
        garmin_service: GarminService 实例（依赖注入）
        processor: DataProcessor 实例（依赖注入）
        gemini: GeminiService 实例（依赖注入）
    
    Returns:
        DailyAnalysisResponse: 包含日期、原始数据摘要和 AI 建议
    """
    logger.info(f"[API] 收到分析请求: date={target_date or 'default'}")
    
    # 确定目标日期（Mock Mode 默认使用 2026-01-01）
    if target_date:
        try:
            # 验证日期格式
            datetime.strptime(target_date, "%Y-%m-%d")
            analysis_date = target_date
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的日期格式: {target_date}。请使用 YYYY-MM-DD 格式。"
            )
    else:
        # Mock Mode 默认使用 2026-01-01（有完整的 20km 跑步数据）
        analysis_date = "2026-01-01" if USE_MOCK_MODE else date.today().isoformat()

    try:
        result = report_service.build_daily_analysis(
            wechat_user_id=wechat_user_id,
            analysis_date=analysis_date,
            force_refresh=force_refresh,
            db=db,
        )
        return DailyAnalysisResponse(**result)
    
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 捕获其他未预期的错误
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Pydantic 请求/响应模型 —— 伤病记录 & 教练记忆
# ---------------------------------------------------------------------------

class InjuryLogCreateRequest(BaseModel):
    """创建伤病日志请求（字段名匹配前端 InjuryLogCreateRequest）"""
    body_part: str
    injury_type: Optional[str] = None
    severity: int  # 1-10（前端用 severity，后端存 pain_level）
    description: Optional[str] = None
    occurred_date: Optional[str] = None  # YYYY-MM-DD（前端用 occurred_date，后端存 log_date）


class InjuryLogUpdateRequest(BaseModel):
    """更新伤病日志请求"""
    severity: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None  # 前端用 is_active(bool)，后端存 is_resolved(反转)


class CoachProfileRequest(BaseModel):
    """更新教练记忆（运动员档案）请求（字段名匹配前端 CoachProfileUpdateRequest）"""
    max_hr: Optional[int] = None
    rest_hr: Optional[int] = None
    vo2max: Optional[float] = None
    lthr: Optional[int] = None
    ftp: Optional[int] = None
    injury_history: Optional[str] = None
    training_preference: Optional[str] = None
    race_target: Optional[str] = None  # 前端用 race_target，后端存 target_race
    race_date: Optional[str] = None  # 前端用 race_date，后端存 target_race_date (YYYY-MM-DD)
    pb_5k_seconds: Optional[int] = None
    pb_10k_seconds: Optional[int] = None
    pb_half_seconds: Optional[int] = None
    pb_full_seconds: Optional[int] = None
    weekly_mileage_goal_km: Optional[float] = None
    target_finish_time_seconds: Optional[int] = None
    notes: Optional[str] = None

# ---------------------------------------------------------------------------
# T7: 伤病记录 API
# ---------------------------------------------------------------------------

@app.post("/api/coach/injury-log")
async def create_injury_log_endpoint(
    req: InjuryLogCreateRequest,
    db: Optional[Session] = Depends(get_db_optional),
):
    """新增伤病日志"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 解析日期（前端传 occurred_date，可选，默认今天）
    log_date_parsed = date.today()
    if req.occurred_date:
        try:
            log_date_parsed = datetime.strptime(req.occurred_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD")

    if not (1 <= req.severity <= 10):
        raise HTTPException(status_code=400, detail="severity 须在 1-10 之间")

    row = create_injury_log(
        db,
        user_id=user.id,
        log_date=log_date_parsed,
        body_part=req.body_part,
        pain_level=req.severity,
        description=req.description,
        is_resolved=0,
        injury_type=req.injury_type,
    )
    db.commit()
    return {
        "id": row.id,
        "body_part": row.body_part,
        "injury_type": row.injury_type,
        "severity": row.pain_level,
        "description": row.description,
        "occurred_date": row.log_date.isoformat(),
        "is_active": not bool(row.is_resolved),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@app.get("/api/coach/injury-log")
async def get_injury_logs_endpoint(
    only_active: bool = False,
    limit: int = 30,
    db: Optional[Session] = Depends(get_db_optional),
):
    """获取伤病日志列表"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    logs = get_injury_logs(db, user_id=user.id, only_active=only_active, limit=limit)
    return [
        {
            "id": log.id,
            "body_part": log.body_part,
            "injury_type": getattr(log, 'injury_type', None),
            "severity": log.pain_level,
            "description": log.description,
            "occurred_date": log.log_date.isoformat(),
            "is_active": not bool(log.is_resolved),
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None,
        }
        for log in logs
    ]


@app.put("/api/coach/injury-log/{log_id}")
async def update_injury_log_endpoint(
    log_id: int,
    req: InjuryLogUpdateRequest,
    db: Optional[Session] = Depends(get_db_optional),
):
    """更新伤病日志"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.severity is not None and not (1 <= req.severity <= 10):
        raise HTTPException(status_code=400, detail="severity 须在 1-10 之间")

    # 前端 is_active(bool) 转后端 is_resolved(int，反转)
    is_resolved_val = None
    if req.is_active is not None:
        is_resolved_val = 0 if req.is_active else 1

    row = update_injury_log(
        db,
        log_id=log_id,
        user_id=user.id,
        pain_level=req.severity,
        description=req.description,
        is_resolved=is_resolved_val,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="伤病记录不存在")

    db.commit()
    return {
        "id": row.id,
        "body_part": row.body_part,
        "injury_type": getattr(row, 'injury_type', None),
        "severity": row.pain_level,
        "description": row.description,
        "occurred_date": row.log_date.isoformat(),
        "is_active": not bool(row.is_resolved),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


# ---------------------------------------------------------------------------
# T8: 教练记忆（运动员档案）API
# ---------------------------------------------------------------------------

@app.get("/api/coach/profile")
async def get_coach_profile_endpoint(
    db: Optional[Session] = Depends(get_db_optional),
):
    """获取运动员档案"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    memory = get_coach_memory(db, user_id=user.id)
    if not memory:
        return {
            "user_id": user.id,
            "max_hr": None,
            "rest_hr": None,
            "vo2max": None,
            "lthr": None,
            "ftp": None,
            "injury_history": None,
            "training_preference": None,
            "race_target": None,
            "race_date": None,
            "pb_5k_seconds": None,
            "pb_10k_seconds": None,
            "pb_half_seconds": None,
            "pb_full_seconds": None,
            "weekly_mileage_goal_km": None,
            "target_finish_time_seconds": None,
            "notes": None,
        }

    return {
        "user_id": memory.user_id,
        "max_hr": memory.max_hr,
        "rest_hr": memory.rest_hr,
        "vo2max": memory.vo2max,
        "lthr": memory.lthr,
        "ftp": memory.ftp,
        "injury_history": memory.injury_history,
        "training_preference": memory.training_preference,
        "race_target": memory.target_race,
        "race_date": memory.target_race_date.isoformat() if memory.target_race_date else None,
        "pb_5k_seconds": memory.pb_5k_seconds,
        "pb_10k_seconds": memory.pb_10k_seconds,
        "pb_half_seconds": memory.pb_half_seconds,
        "pb_full_seconds": memory.pb_full_seconds,
        "weekly_mileage_goal_km": memory.weekly_mileage_goal_km,
        "target_finish_time_seconds": memory.target_finish_time_seconds,
        "notes": memory.notes,
    }


@app.put("/api/coach/profile")
async def update_coach_profile_endpoint(
    req: CoachProfileRequest,
    db: Optional[Session] = Depends(get_db_optional),
):
    """创建或更新运动员档案"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 解析日期（前端传 race_date）
    race_date_parsed = None
    if req.race_date:
        try:
            race_date_parsed = datetime.strptime(req.race_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="race_date 格式无效，请使用 YYYY-MM-DD")

    memory = upsert_coach_memory(
        db,
        user_id=user.id,
        target_race=req.race_target,
        target_race_date=race_date_parsed,
        pb_5k_seconds=req.pb_5k_seconds,
        pb_10k_seconds=req.pb_10k_seconds,
        pb_half_seconds=req.pb_half_seconds,
        pb_full_seconds=req.pb_full_seconds,
        weekly_mileage_goal_km=req.weekly_mileage_goal_km,
        target_finish_time_seconds=req.target_finish_time_seconds,
        notes=req.notes,
        max_hr=req.max_hr,
        rest_hr=req.rest_hr,
        vo2max=req.vo2max,
        lthr=req.lthr,
        ftp=req.ftp,
        injury_history=req.injury_history,
        training_preference=req.training_preference,
    )
    db.commit()

    return {
        "user_id": memory.user_id,
        "max_hr": memory.max_hr,
        "rest_hr": memory.rest_hr,
        "vo2max": memory.vo2max,
        "lthr": memory.lthr,
        "ftp": memory.ftp,
        "injury_history": memory.injury_history,
        "training_preference": memory.training_preference,
        "race_target": memory.target_race,
        "race_date": memory.target_race_date.isoformat() if memory.target_race_date else None,
        "pb_5k_seconds": memory.pb_5k_seconds,
        "pb_10k_seconds": memory.pb_10k_seconds,
        "pb_half_seconds": memory.pb_half_seconds,
        "pb_full_seconds": memory.pb_full_seconds,
        "weekly_mileage_goal_km": memory.weekly_mileage_goal_km,
        "target_finish_time_seconds": memory.target_finish_time_seconds,
        "notes": memory.notes,
    }


# ==================== T4: 晨间报告 ====================

@app.get("/api/coach/morning-report")
async def morning_report_endpoint(
    target_date: Optional[str] = None,
    db: Optional[Session] = Depends(get_db_optional),
    service: CoachReportService = Depends(get_coach_report_service),
):
    """晨间报告：基于昨晚睡眠和近期训练负荷，给出今日训练建议。"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")
    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    dt = date.fromisoformat(target_date) if target_date else date.today()
    try:
        result = service.build_morning_report(db, user.id, dt)
        return result
    except Exception as e:
        logger.error(f"晨间报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"晨间报告生成失败: {str(e)}")


# ==================== T5: 晚间复盘 ====================

@app.get("/api/coach/evening-review")
async def evening_review_endpoint(
    target_date: Optional[str] = None,
    db: Optional[Session] = Depends(get_db_optional),
    service: CoachReportService = Depends(get_coach_report_service),
):
    """晚间复盘：基于今日训练数据，给出恢复建议和明日展望。"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")
    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    dt = date.fromisoformat(target_date) if target_date else date.today()
    try:
        result = service.build_evening_review(db, user.id, dt)
        return result
    except Exception as e:
        logger.error(f"晚间复盘生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"晚间复盘生成失败: {str(e)}")


# ==================== T6: 周度总结 ====================

@app.get("/api/coach/weekly-summary")
async def weekly_summary_endpoint(
    target_date: Optional[str] = None,
    db: Optional[Session] = Depends(get_db_optional),
    service: CoachReportService = Depends(get_coach_report_service),
):
    """周度总结：过去 7 天训练回顾和下周训练方向建议。"""
    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")
    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定")
    user = db.query(User).filter(User.garmin_email == credential.garmin_email).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    dt = date.fromisoformat(target_date) if target_date else date.today()
    try:
        result = service.build_weekly_summary(db, user.id, dt)
        return result
    except Exception as e:
        logger.error(f"周度总结生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"周度总结生成失败: {str(e)}")


# ==================== Garmin Profile 同步 ====================

@app.post("/api/coach/sync-garmin-profile")
async def sync_garmin_profile_endpoint(
    db: Optional[Session] = Depends(get_db_optional),
):
    """从 Garmin 同步用户体能数据到运动员档案（max_hr, rest_hr, vo2max, PB）。"""
    if settings.USE_MOCK_MODE:
        raise HTTPException(status_code=503, detail="Mock 模式下不支持同步 Garmin 档案")

    from backend.app.utils.crypto import decrypt_text

    if not db:
        raise HTTPException(status_code=500, detail="数据库不可用")

    credential = get_garmin_credential(db, wechat_user_id=1)
    if not credential:
        raise HTTPException(status_code=404, detail="Garmin 未绑定，请先绑定 Garmin 账号")

    try:
        garmin_password = decrypt_text(credential.garmin_password)
        garmin_client = GarminClient(
            email=credential.garmin_email,
            password=garmin_password,
            is_cn=bool(credential.is_cn),
        )
    except Exception as e:
        logger.error(f"Garmin 客户端初始化失败: {e}")
        raise HTTPException(status_code=500, detail=f"Garmin 连接失败: {str(e)}")

    today_str = date.today().strftime("%Y-%m-%d")
    synced_fields: Dict[str, Any] = {}

    # 获取 max_hr, resting_hr, vo2max
    try:
        profile_data = garmin_client.get_user_profile_data(today_str)
        if profile_data.get("max_heart_rate"):
            synced_fields["max_hr"] = int(profile_data["max_heart_rate"])
        if profile_data.get("resting_heart_rate"):
            synced_fields["rest_hr"] = int(profile_data["resting_heart_rate"])
        if profile_data.get("vo2_max"):
            synced_fields["vo2max"] = float(profile_data["vo2_max"])

        # 解析 PB 数据
        prs = profile_data.get("personal_records")
        if prs and isinstance(prs, list):
            for pr in prs:
                if not isinstance(pr, dict):
                    continue
                type_id = pr.get("personalRecordTypeId") or pr.get("typeId")
                value = pr.get("value")
                if type_id is None or value is None:
                    continue
                # Garmin PB typeId: 1=1mile, 2=3k, 3=5k, 4=10k, 5=half, 6=marathon
                if type_id == 3:
                    synced_fields["pb_5k_seconds"] = int(value)
                elif type_id == 4:
                    synced_fields["pb_10k_seconds"] = int(value)
                elif type_id == 5:
                    synced_fields["pb_half_seconds"] = int(value)
                elif type_id == 6:
                    synced_fields["pb_full_seconds"] = int(value)
    except Exception as e:
        logger.warning(f"Garmin profile 数据获取部分失败: {e}")

    if not synced_fields:
        return {"success": True, "message": "未能从 Garmin 获取到可同步的数据", "synced_fields": {}}

    # 写入 coach_memory
    try:
        upsert_coach_memory(db, wechat_user_id=1, **synced_fields)
    except Exception as e:
        logger.error(f"Coach memory 更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据保存失败: {str(e)}")

    return {"success": True, "message": f"已同步 {len(synced_fields)} 项数据", "synced_fields": synced_fields}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
