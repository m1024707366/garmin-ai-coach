"""
Application Configuration
"""
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GARMIN_EMAIL: str
    GARMIN_PASSWORD: str
    GEMINI_API_KEY: Optional[str] = None  # 保留兼容，可选
    GARMIN_IS_CN: bool = False  # True = connect.garmin.cn（中国），False = connect.garmin.com（国际）
    PROXY_URL: Optional[str] = None  # 代理 URL，用于访问 Google API（例如：http://127.0.0.1:7890）

    # WeChat mini program
    WECHAT_MINI_APPID: Optional[str] = None
    WECHAT_MINI_SECRET: Optional[str] = None
    WECHAT_SUBSCRIBE_TEMPLATE_ID: Optional[str] = None
    WECHAT_SUBSCRIBE_PAGE: str = "pages/index/index"
    WECHAT_TOKEN_CACHE_SECONDS: int = 7000
    WECHAT_AUTH_SECRET: Optional[str] = None
    WECHAT_ACCESS_TOKEN_EXPIRES_SECONDS: int = 86400 * 30

    # Garmin credential encryption
    GARMIN_CRED_ENCRYPTION_KEY: Optional[str] = None

    # Database
    DATABASE_URL: Optional[str] = None  # e.g. mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4

    # Gemini
    GEMINI_LIST_MODELS: bool = False  # 调试用：启动时列出可用模型
    GEMINI_MODEL_NAME: str = "gemini-3-flash-preview"

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL_NAME: str = "deepseek-reasoner"  # R1 推理模型
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_NAME: str = "gpt-3.5-turbo"
    OPENAI_BASE_URL: Optional[str] = None  # 自定义OpenAI API地址
    
    LLM_PROVIDER: str = "deepseek"  # "deepseek", "gemini" 或 "openai"
    # Runtime behavior
    USE_MOCK_MODE: bool = False
    ANALYSIS_CACHE_HOURS: int = 24
    ENABLE_GARMIN_POLLING: bool = False
    GARMIN_POLL_INTERVAL_MINUTES: int = 30
    INITIAL_BIND_BACKFILL_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略多余的配置项


settings = Settings()
