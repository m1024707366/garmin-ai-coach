"""
Garmin Client
封装 Garmin Connect API 客户端，提供健康数据和训练计划获取功能。
"""
import glob
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from garminconnect import Garmin

from src.core.config import settings

# 初始化 logger
logger = logging.getLogger(__name__)


def _seconds_to_hh_mm(seconds: Optional[float]) -> str:
    """将秒数转换为 "H:MM" 格式。"""
    if seconds is None or not isinstance(seconds, (int, float)) or seconds < 0:
        return "N/A"
    try:
        total_seconds = int(round(float(seconds)))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}:{minutes:02d}"
        return f"{minutes}"
    except (TypeError, ValueError):
        return "N/A"


class GarminClient:
    """
    Garmin Connect API 客户端封装类。
    提供健康数据和训练计划获取功能。
    """

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None, is_cn: Optional[bool] = None):
        """
        初始化 Garmin 客户端。

        Args:
            email: Garmin 邮箱，默认从 settings 读取
            password: Garmin 密码，默认从 settings 读取
            is_cn: 是否使用中国区，默认从 settings 读取
        """
        self.email = email or settings.GARMIN_EMAIL
        self.password = password or settings.GARMIN_PASSWORD
        self.is_cn = is_cn if is_cn is not None else settings.GARMIN_IS_CN
        self.client = Garmin(self.email, self.password, is_cn=self.is_cn)
        self.client.login()

    def get_health_stats(self, date_str: str) -> Optional[Dict[str, Any]]:
        """
        获取指定日期的健康数据。

        合并以下数据源：
        - get_stats_and_body: 基础健康数据（活动、身体成分）
        - get_user_summary: 压力、静息心率、身体电量等
        - get_sleep_data: 睡眠数据（注意：睡眠数据通常属于"前一天晚上"，但 Garmin 归档在起床当天）

        Args:
            date_str: 日期字符串，格式 "YYYY-MM-DD"

        Returns:
            合并后的健康数据字典，如果获取失败返回 None
        """
        result: Dict[str, Any] = {
            "date": date_str,
        }

        # 1. 获取基础健康数据 (stats_and_body)
        try:
            stats_body = self.client.get_stats_and_body(date_str)
            if stats_body:
                result.update(stats_body)
        except Exception as e:
            # 如果失败，继续尝试其他数据源
            result["stats_and_body_error"] = str(e)

        # 2. 获取用户摘要 (user_summary)（增强提取）
        try:
            user_summary = self.client.get_user_summary(date_str)
            if user_summary:
                # 提取关键字段
                if "restingHeartRate" in user_summary:
                    result["resting_heart_rate"] = user_summary.get("restingHeartRate")
                
                # HRV Status
                hrv_status = user_summary.get("hrvStatus") or user_summary.get("hrvStatusDTO")
                if hrv_status:
                    if isinstance(hrv_status, dict):
                        result["hrv_status"] = hrv_status.get("status") or hrv_status.get("value")
                    else:
                        result["hrv_status"] = str(hrv_status)
                
                # Body Battery: chargedValue 和 drainedValue
                if "bodyBatteryMostRecentValue" in user_summary:
                    result["body_battery"] = user_summary.get("bodyBatteryMostRecentValue")
                
                # 尝试从 bodyBatteryDTO 或其他字段获取 charged/drained
                bb_dto = user_summary.get("bodyBatteryDTO") or user_summary.get("bodyBattery")
                if isinstance(bb_dto, dict):
                    if "chargedValue" in bb_dto:
                        result["body_battery_charged"] = bb_dto.get("chargedValue")
                    if "drainedValue" in bb_dto:
                        result["body_battery_drained"] = bb_dto.get("drainedValue")
                
                # Stress: averageStressLevel
                stress_level = (
                    user_summary.get("averageStressLevel")
                    or user_summary.get("stressLevel")
                    or user_summary.get("stress")
                )
                if stress_level is not None and isinstance(stress_level, (int, float)):
                    result["average_stress_level"] = int(stress_level)
                
                if "stressQualifier" in user_summary:
                    result["stress_qualifier"] = user_summary.get("stressQualifier")
                
                if "totalSteps" in user_summary:
                    result["total_steps"] = user_summary.get("totalSteps")
                
                # 保留完整的 user_summary 作为备用
                result["user_summary"] = user_summary
        except Exception as e:
            result["user_summary_error"] = str(e)

        # 3. 获取睡眠数据（增强提取）
        try:
            sleep_data = self.client.get_sleep_data(date_str)
            if sleep_data:
                # 提取关键字段
                daily_sleep = sleep_data.get("dailySleepDTO") or {}
                if "sleepTimeSeconds" in daily_sleep:
                    result["sleep_time_seconds"] = daily_sleep.get("sleepTimeSeconds")
                    # 转换为小时
                    sleep_time_sec = daily_sleep.get("sleepTimeSeconds")
                    if sleep_time_sec is not None and isinstance(sleep_time_sec, (int, float)):
                        result["sleep_time_hours"] = round(float(sleep_time_sec) / 3600, 1)
                
                # 睡眠分数
                if "sleepScores" in daily_sleep:
                    scores = daily_sleep.get("sleepScores") or {}
                    overall = scores.get("overall") or {}
                    if isinstance(overall, dict) and "value" in overall:
                        result["sleep_score"] = overall.get("value")
                elif "sleepScore" in daily_sleep:
                    result["sleep_score"] = daily_sleep.get("sleepScore")
                elif "sleepScore" in sleep_data:
                    result["sleep_score"] = sleep_data.get("sleepScore")
                
                # 深睡时长（秒和格式化）
                deep_sleep_sec = daily_sleep.get("deepSleepSeconds")
                if deep_sleep_sec is not None and isinstance(deep_sleep_sec, (int, float)):
                    result["deep_sleep_seconds"] = float(deep_sleep_sec)
                    result["deep_sleep_hh_mm"] = _seconds_to_hh_mm(deep_sleep_sec)
                
                # REM 睡眠时长（秒和格式化）
                rem_sleep_sec = daily_sleep.get("remSleepSeconds")
                if rem_sleep_sec is not None and isinstance(rem_sleep_sec, (int, float)):
                    result["rem_sleep_seconds"] = float(rem_sleep_sec)
                    result["rem_sleep_hh_mm"] = _seconds_to_hh_mm(rem_sleep_sec)
                
                # 浅睡时长（秒和格式化）
                light_sleep_sec = daily_sleep.get("lightSleepSeconds")
                if light_sleep_sec is not None and isinstance(light_sleep_sec, (int, float)):
                    result["light_sleep_seconds"] = float(light_sleep_sec)
                    result["light_sleep_hh_mm"] = _seconds_to_hh_mm(light_sleep_sec)
                
                # 清醒时长（秒和格式化）
                awake_sleep_sec = daily_sleep.get("awakeSleepSeconds")
                if awake_sleep_sec is not None and isinstance(awake_sleep_sec, (int, float)):
                    result["awake_sleep_seconds"] = float(awake_sleep_sec)
                    result["awake_sleep_hh_mm"] = _seconds_to_hh_mm(awake_sleep_sec)
                
                # 睡眠质量评语
                sleep_quality = (
                    daily_sleep.get("sleepQualityTypeKey")
                    or daily_sleep.get("sleepQuality")
                    or sleep_data.get("sleepQualityTypeKey")
                    or sleep_data.get("sleepQuality")
                )
                if sleep_quality:
                    result["sleep_quality"] = str(sleep_quality)
                
                # 保留完整的 sleep_data 作为备用
                result["sleep_data"] = sleep_data
        except Exception as e:
            result["sleep_data_error"] = str(e)

        # 如果所有数据源都失败，返回 None
        if all(key.endswith("_error") for key in result.keys() if key != "date"):
            return None

        return result

    def get_training_plan(self, start_date_str: str, days: int = 3) -> List[Dict[str, Any]]:
        """
        获取未来几天的训练计划。

        计算结束日期，调用日历 API，筛选出 training 类型的条目。

        Args:
            start_date_str: 开始日期，格式 "YYYY-MM-DD"
            days: 获取未来几天的计划，默认 3 天

        Returns:
            训练计划列表，如果获取失败返回空列表
        """
        try:
            # 计算结束日期
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = start_date + timedelta(days=days - 1)
            end_date_str = end_date.strftime("%Y-%m-%d")

            # 尝试使用 connectapi 直接调用日历 API
            # 由于 garminconnect 库可能没有 get_calendar 方法，我们尝试多个可能的 API 路径

            # 方法1: 尝试使用 connectapi 获取日历数据
            calendar_urls = [
                "/calendar-service/calendar/day",
                "/calendar-service/calendar/events",
                "/calendar-service/calendar",
            ]

            for calendar_url in calendar_urls:
                try:
                    # 获取每一天的日历数据
                    calendar_entries: List[Dict[str, Any]] = []
                    current_date = start_date
                    while current_date <= end_date:
                        date_str = current_date.strftime("%Y-%m-%d")
                        try:
                            # 尝试调用日历 API
                            params = {"calendarDate": date_str}
                            day_data = self.client.connectapi(calendar_url, params=params)
                            if day_data and isinstance(day_data, list):
                                calendar_entries.extend(day_data)
                            elif day_data and isinstance(day_data, dict):
                                # 如果返回的是字典，可能包含 events 或类似字段
                                events = (
                                    day_data.get("events")
                                    or day_data.get("calendarEvents")
                                    or day_data.get("items")
                                    or []
                                )
                                if isinstance(events, list):
                                    calendar_entries.extend(events)
                        except Exception:
                            # 如果这个日期失败，继续下一个日期
                            pass
                        current_date += timedelta(days=1)

                    # 如果获取到数据，筛选出 training 类型的条目
                    if calendar_entries:
                        training_plans = []
                        for entry in calendar_entries:
                            if isinstance(entry, dict):
                                # 检查是否为训练类型
                                entry_type = (
                                    entry.get("type")
                                    or entry.get("eventType")
                                    or entry.get("activityType")
                                    or entry.get("eventTypeKey")
                                    or ""
                                )
                                type_str = str(entry_type).lower()
                                if (
                                    "training" in type_str
                                    or "workout" in type_str
                                    or "exercise" in type_str
                                ):
                                    training_plans.append(entry)

                        if training_plans:
                            return training_plans

                except Exception:
                    # 如果这个 URL 失败，尝试下一个
                    continue

            # 方法2: 尝试使用 get_goals 获取未来的训练目标
            try:
                goals = self.client.get_goals(status="future", start=1, limit=30)
                training_plans = []
                for goal in goals or []:
                    if isinstance(goal, dict):
                        goal_date = goal.get("targetDate") or goal.get("startDate") or goal.get("date")
                        if goal_date:
                            # 检查日期是否在范围内
                            try:
                                goal_date_obj = datetime.strptime(str(goal_date)[:10], "%Y-%m-%d")
                                if start_date <= goal_date_obj <= end_date:
                                    training_plans.append(goal)
                            except (ValueError, TypeError):
                                pass
                return training_plans
            except Exception:
                pass

            # 如果所有方法都失败，返回空列表
            return []

        except Exception as e:
            # 处理任何异常，返回空列表
            return []

    def get_mock_data(self, target_date: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        从本地 JSON 文件读取模拟数据（Mock Mode），用于快速开发测试。
        
        优先从 backend/app/data/mock_garmin.json 读取，如果找不到指定日期，
        则尝试从项目根目录的 garmin_monthly_*.json 文件读取。
        
        Args:
            target_date: 目标日期，格式 "YYYY-MM-DD"
        
        Returns:
            元组 (activity, health, plan):
            - activity: 活动数据字典（如果有），格式与 GarminService.get_daily_data 返回的 activities[0] 一致
            - health: 健康数据字典，格式与 get_health_stats 返回的一致
            - plan: 训练计划列表（模拟数据返回空列表或简单计划）
        """
        # 首先尝试从 backend/app/data/mock_garmin.json 读取
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mock_file = os.path.join(current_dir, "..", "..", "..", "backend", "app", "data", "mock_garmin.json")
        
        # 如果文件不存在，尝试相对路径
        if not os.path.exists(mock_file):
            mock_file = os.path.join(current_dir, "..", "data", "mock_garmin.json")
        
        mock_data = None
        target_day = None
        
        # 尝试读取 mock_garmin.json
        if os.path.exists(mock_file):
            logger.info(f"[Garmin] 正在读取本地 Mock 数据: {mock_file}")
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
                logger.warning(f"[Garmin] 读取 Mock 数据文件失败: {e}")
        
        # 如果在 mock_garmin.json 中找不到，尝试从项目根目录的 garmin_monthly_*.json 读取
        if not target_day:
            # 获取项目根目录（从 backend/app/services/garmin_client.py 向上 3 层）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 查找所有 garmin_monthly_*.json 文件
            monthly_files = glob.glob(os.path.join(project_root, "garmin_monthly_*.json"))
            
            # 按修改时间排序，最新的优先
            monthly_files.sort(key=os.path.getmtime, reverse=True)
            
            for monthly_file in monthly_files:
                logger.info(f"[Garmin] 尝试从项目根目录读取数据: {monthly_file}")
                try:
                    with open(monthly_file, "r", encoding="utf-8") as f:
                        monthly_data = json.load(f)
                    
                    # 在 days 数组中查找匹配的日期
                    days = monthly_data.get("days", [])
                    for day in days:
                        if day.get("date") == target_date:
                            target_day = day
                            mock_data = monthly_data  # 保存数据以便后续使用
                            logger.info(f"[Garmin] 在 {os.path.basename(monthly_file)} 中找到日期 {target_date} 的数据")
                            break
                    
                    if target_day:
                        break
                except Exception as e:
                    logger.warning(f"[Garmin] 读取 {monthly_file} 失败: {e}")
                    continue
        
        if not target_day:
            # 如果找不到指定日期，返回空数据
            logger.warning(f"[Garmin] 未找到日期 {target_date} 的数据")
            return None, None, []
        
        logger.info(f"[Garmin] 成功加载日期 {target_date} 的数据")
        
        # 提取活动数据（第一个活动）
        activity = None
        activities = target_day.get("activities", [])
        if activities and len(activities) > 0:
            activity = activities[0]  # 使用第一个活动
        
        # 构造健康数据
        health: Dict[str, Any] = {
            "date": target_date,
        }
        
        summary = target_day.get("summary", {})
        sleep_info = summary.get("sleep", {})
        
        # 睡眠数据
        if sleep_info:
            health["sleep_time_seconds"] = sleep_info.get("total_duration")
            health["sleep_time_hours"] = round(sleep_info.get("total_duration", 0) / 3600, 1) if sleep_info.get("total_duration") else None
            health["sleep_score"] = sleep_info.get("sleep_score")
            health["deep_sleep_seconds"] = sleep_info.get("deep_sleep_seconds")
            health["deep_sleep_hh_mm"] = _seconds_to_hh_mm(sleep_info.get("deep_sleep_seconds"))
            health["rem_sleep_seconds"] = sleep_info.get("rem_sleep_seconds")
            health["rem_sleep_hh_mm"] = _seconds_to_hh_mm(sleep_info.get("rem_sleep_seconds"))
            health["light_sleep_seconds"] = sleep_info.get("light_sleep_seconds")
            health["light_sleep_hh_mm"] = _seconds_to_hh_mm(sleep_info.get("light_sleep_seconds"))
            health["awake_sleep_seconds"] = sleep_info.get("awake_sleep_seconds")
            health["awake_sleep_hh_mm"] = _seconds_to_hh_mm(sleep_info.get("awake_sleep_seconds"))
            health["recovery_quality_percent"] = sleep_info.get("recovery_quality_percent")
        
        # 静息心率
        health["resting_heart_rate"] = summary.get("resting_heart_rate")
        
        # Body Battery（从 summary 提取，如果没有则使用默认值）
        health["body_battery"] = summary.get("body_battery", 60)  # 默认值 60
        health["body_battery_charged"] = None  # Mock 数据中没有，设为 None
        health["body_battery_drained"] = None  # Mock 数据中没有，设为 None
        
        # HRV Status
        health["hrv_status"] = None  # Mock 数据中没有，设为 None
        
        # 压力数据（从 summary 提取，如果没有则使用默认值）
        health["average_stress_level"] = summary.get("average_stress_level", 35)  # 默认值 35
        health["stress_qualifier"] = summary.get("stress_qualifier", "BALANCED")  # 默认值
        
        # 训练计划（返回简单的模拟计划）
        plan: List[Dict[str, Any]] = [
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

    def get_user_profile_data(self, date_str: str) -> Dict[str, Any]:
        """
        获取用户个人基础数据，用于个性化 AI 分析。

        合并以下数据源：
        - get_body_composition: 体重、BMI、体脂率等
        - get_max_metrics: VO2Max、最大心率等运动能力指标
        - get_heart_rates: 心率区间数据
        - get_training_status: 训练状态
        - get_training_readiness: 训练准备度
        - get_personal_record: 个人最佳记录
        - get_race_predictions: 比赛预测

        Args:
            date_str: 日期字符串，格式 "YYYY-MM-DD"

        Returns:
            合并后的用户个人数据字典
        """
        result: Dict[str, Any] = {
            "date": date_str,
        }

        # 1. 获取身体成分数据
        try:
            body_comp = self.client.get_body_composition(date_str)
            if body_comp:
                if "weight" in body_comp:
                    result["weight_kg"] = body_comp.get("weight")
                if "bmi" in body_comp:
                    result["bmi"] = body_comp.get("bmi")
                if "bodyFat" in body_comp:
                    result["body_fat_percent"] = body_comp.get("bodyFat")
                result["body_composition"] = body_comp
        except Exception as e:
            result["body_composition_error"] = str(e)

        # 2. 获取最大运动指标
        try:
            max_metrics = self.client.get_max_metrics(date_str)
            if max_metrics:
                if "vo2Max" in max_metrics:
                    result["vo2_max"] = max_metrics.get("vo2Max")
                if "maxHeartRate" in max_metrics:
                    result["max_heart_rate"] = max_metrics.get("maxHeartRate")
                if "restingHeartRate" in max_metrics:
                    result["resting_heart_rate"] = max_metrics.get("restingHeartRate")
                result["max_metrics"] = max_metrics
        except Exception as e:
            result["max_metrics_error"] = str(e)

        # 3. 获取心率区间数据
        try:
            heart_rates = self.client.get_heart_rates(date_str)
            if heart_rates:
                result["heart_rates"] = heart_rates
        except Exception as e:
            result["heart_rates_error"] = str(e)

        # 4. 获取训练状态
        try:
            training_status = self.client.get_training_status(date_str)
            if training_status:
                if "trainingStatus" in training_status:
                    result["training_status"] = training_status.get("trainingStatus")
                if "trainingEffect" in training_status:
                    result["training_effect"] = training_status.get("trainingEffect")
                if "activityEffect" in training_status:
                    result["activity_effect"] = training_status.get("activityEffect")
                result["training_status_data"] = training_status
        except Exception as e:
            result["training_status_error"] = str(e)

        # 5. 获取训练准备度
        try:
            readiness = self.client.get_training_readiness(date_str)
            if readiness:
                if "trainingReadiness" in readiness:
                    result["training_readiness"] = readiness.get("trainingReadiness")
                result["training_readiness_data"] = readiness
        except Exception as e:
            result["training_readiness_error"] = str(e)

        # 6. 获取个人最佳记录
        try:
            prs = self.client.get_personal_record()
            if prs:
                result["personal_records"] = prs
        except Exception as e:
            result["personal_record_error"] = str(e)

        # 7. 获取比赛预测
        try:
            predictions = self.client.get_race_predictions(date_str, date_str)
            if predictions:
                result["race_predictions"] = predictions
        except Exception as e:
            result["race_predictions_error"] = str(e)

        return result
