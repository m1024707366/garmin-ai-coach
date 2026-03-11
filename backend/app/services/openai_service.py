"""
OpenAI Service
封装 OpenAI API，作为 Gemini 和 DeepSeek 的替代方案。
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

from openai import OpenAI

from src.core.config import settings

# 复用 Gemini 的教练系统提示词
from backend.app.services.gemini_service import COACH_SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    封装 OpenAI API，提供与 GeminiService 相同的接口。
    使用 OpenAI SDK 调用。
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化 OpenAI 服务。

        Args:
            model_name: 模型名称（可选，默认使用 settings.OPENAI_MODEL_NAME）
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，请在 .env 中设置")

        self.model_name = model_name or settings.OPENAI_MODEL_NAME
        self._client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

        logger.info(f"[OpenAI] 使用模型: {self.model_name}")

    @staticmethod
    def _parse_json_payload(text: str) -> Optional[dict]:
        """
        从 AI 响应文本中解析 JSON，复用 GeminiService 的解析逻辑。
        """
        raw = (text or "").strip()
        if not raw:
            return None

        # 1) 直接 JSON
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        # 2) ```json ... ``` 代码块
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1).strip()
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

        # 3) 第一个 {...} 对象
        first = raw.find("{")
        last = raw.rfind("}")
        if first != -1 and last > first:
            candidate = raw[first : last + 1]
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                return None
        return None

    def _call_api(
        self,
        *,
        messages: list[dict],
        timeout: int = 60,
        max_retries: int = 2,
    ) -> str:
        """
        通用 API 调用封装，带重试机制。

        Args:
            messages: 消息列表（OpenAI 格式）
            timeout: 超时秒数
            max_retries: 最大重试次数

        Returns:
            AI 回复文本
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": self.model_name,
                    "messages": messages,
                    "timeout": timeout,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                }

                response = self._client.chat.completions.create(**kwargs)

                # 提取回复内容
                choice = response.choices[0]
                result_text = choice.message.content

                if result_text:
                    result_text = result_text.strip()
                    # 清理可能的代码块标记
                    if result_text.startswith("```"):
                        lines = result_text.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        result_text = "\n".join(lines).strip()

                    logger.info(f"[OpenAI] 响应生成完毕 (模型: {self.model_name})")
                    return result_text
                else:
                    raise ValueError("响应中没有有效的文本内容")

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[OpenAI] 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue

        logger.error(f"[OpenAI] 所有重试均失败: {last_error}")
        raise RuntimeError(f"OpenAI API 调用失败: {last_error}")

    def chat(self, full_prompt: str) -> str:
        """
        纯对话调用，直接传入完整提示词。

        接口与 GeminiService.chat() 保持一致。

        Args:
            full_prompt: 已组装完成的完整提示词（包含系统指令 + 上下文 + 用户消息）

        Returns:
            AI 回复文本
        """
        if not full_prompt or not full_prompt.strip():
            return "我没有收到你的消息，再说一遍？"

        logger.info("[OpenAI] 开始聊天请求...")

        messages = [
            {"role": "system", "content": "你是一位专业的跑步教练和运动科学顾问。"},
            {"role": "user", "content": full_prompt},
        ]

        try:
            return self._call_api(messages=messages, timeout=60)
        except RuntimeError:
            return "对话暂不可用，请稍后重试。"

    def analyze_training(self, daily_report_md: str) -> str:
        """
        分析训练数据，返回 AI 教练建议。

        接口与 GeminiService.analyze_training() 保持一致。

        Args:
            daily_report_md: 由 DataProcessor 生成的 Markdown 格式日报

        Returns:
            AI 生成的分析建议文本（Markdown 格式）
        """
        if not daily_report_md or not daily_report_md.strip():
            logger.warning("[OpenAI] 收到空数据，无法进行分析")
            return "## 📊 分析结果\n\n暂无数据，无法进行分析。"

        logger.info("[OpenAI] 开始请求训练分析...")

        full_prompt = f"""{COACH_SYSTEM_INSTRUCTION}

=== 用户今日数据 ===

{daily_report_md}

请按照以下结构输出：
- **身体状态评估**
- **跑步表现分析**（如果有跑步数据）
- **训练建议**
"""

        messages = [
            {"role": "system", "content": COACH_SYSTEM_INSTRUCTION},
            {
                "role": "user",
                "content": f"=== 用户今日数据 ===\n\n{daily_report_md}\n\n" +
                "请按照以下结构输出：\n" +
                "- **身体状态评估**\n" +
                "- **跑步表现分析**（如果有跑步数据）\n" +
                "- **训练建议**",
            },
        ]

        try:
            return self._call_api(messages=messages, timeout=60)
        except RuntimeError as e:
            error_msg = str(e)
            logger.error(f"[OpenAI] 训练分析失败: {error_msg}")
            return f"""## 📊 分析结果

教练正在看表，稍后再试...

**错误信息**: {error_msg}

**建议**: 请检查网络连接或稍后重试。
"""

    def analyze_training_with_fallback(self, daily_report_md: str) -> str:
        """
        分析训练数据（兼容接口）。
        OpenAI 无需模型降级，直接调用 analyze_training。
        """
        return self.analyze_training(daily_report_md)

    def generate_home_summary_brief(
        self,
        *,
        week_stats: dict,
        month_stats: dict,
        run_count: int,
        sleep_days: int,
    ) -> dict[str, Optional[str]]:
        """
        生成首页简评。

        接口与 GeminiService.generate_home_summary_brief() 保持一致。
        """
        if run_count < 3 or sleep_days < 3:
            return {"week": None, "month": None}

        prompt_payload = {
            "run_count_30d": run_count,
            "sleep_days_30d": sleep_days,
            "week_stats": week_stats,
            "month_stats": month_stats,
        }
        prompt = (
            "你是跑步教练，请根据数据输出简短首页简评。\n" +
            '仅返回 JSON：{"week": string|null, "month": string|null}。\n' +
            "要求：每条不超过 40 字，不要换行，不要 Markdown。\n" +
            f"输入数据: {json.dumps(prompt_payload, ensure_ascii=False)}"
        )

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的跑步教练。仅返回 JSON 格式。",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            result_text = self._call_api(messages=messages, timeout=30)
            data = self._parse_json_payload(result_text)
            if not isinstance(data, dict):
                raise ValueError("OpenAI 返回非 JSON 内容")
            week = data.get("week") if isinstance(data, dict) else None
            month = data.get("month") if isinstance(data, dict) else None
            return {
                "week": str(week) if week else None,
                "month": str(month) if month else None,
            }
        except Exception as e:
            logger.warning(f"[OpenAI] Home summary brief failed: {e}")
            return {"week": None, "month": None}
