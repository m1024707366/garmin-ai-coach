from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.db.crud import (
    upsert_home_summary,
)
from backend.app.db.models import User
from backend.app.services.home_summary_service import HomeSummaryService
from backend.app.services.report_service import ReportService


logger = logging.getLogger(__name__)


def detect_new_data(sync_state: Dict[str, Any], latest: Dict[str, Any]) -> bool:
    if not sync_state or not latest:
        return False
    last_activity_id = sync_state.get("last_activity_id")
    last_summary_date = sync_state.get("last_summary_date")

    latest_activity_id = latest.get("latest_activity_id")
    latest_summary_date = latest.get("latest_summary_date")

    if latest_activity_id and latest_activity_id != last_activity_id:
        return True
    if latest_summary_date and latest_summary_date != last_summary_date:
        return True
    return False


def build_template_data(report_date: str, summary: str) -> Dict[str, Dict[str, str]]:
    # 模板字段：运动记录、时间、备注
    # thing01: 运动记录 (20字内)
    # time01: 时间
    # remark01: 备注
    return {
        "thing01": {"value": "跑步数据同步完成"},
        "time01": {"value": report_date},
        "remark01": {"value": summary[:20] if summary else "点击查看详细报告"},
    }

def _build_latest_snapshot() -> Dict[str, Any]:
    now_date = datetime.now().date().isoformat()
    return {
        "latest_activity_id": None,
        "latest_summary_date": now_date,
    }


def poll_garmin_for_user(
    *,
    db: Session,
    user_id: int,
    report_service: ReportService,
    home_summary_service: HomeSummaryService,
) -> None:
    # 获取用户
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        return

    latest_snapshot = _build_latest_snapshot()
    analysis_date = latest_snapshot.get("latest_summary_date") or datetime.now().date().isoformat()

    result = report_service.build_daily_analysis(
        user_id=user_id,
        analysis_date=analysis_date,
        force_refresh=True,
        db=db,
    )

    home_summary_payload = home_summary_service.build_summary(
        db=db,
        user_id=user_id,
        include_ai_brief=False,
    )
    upsert_home_summary(
        db,
        user_id=user_id,
        latest_run_json=home_summary_payload.get("latest_run"),
        week_stats_json=home_summary_payload.get("week_stats"),
        month_stats_json=home_summary_payload.get("month_stats"),
        ai_brief_json=None,
    )

    db.commit()
    _ = result


def poll_garmin(db: Session) -> None:
    report_service = ReportService()
    home_summary_service = HomeSummaryService()

    users = db.query(User).all()
    for user in users:
        try:
            poll_garmin_for_user(
                db=db,
                user_id=user.id,
                report_service=report_service,
                home_summary_service=home_summary_service,
            )
        except Exception as e:
            logger.warning(f"[Poll] failed for user {user.id}: {e}")
