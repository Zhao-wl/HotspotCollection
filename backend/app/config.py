"""
应用配置：从环境变量加载，不硬编码密钥。
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """硅基流动 API（用于 LangExtract / 关键词提取）。"""

    siliconflow_api_key: str = ""
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_model: str = "Qwen/Qwen3-8B"

    class Config:
        env_prefix = "SILICONFLOW_"
        env_file = ".env"
        extra = "ignore"


settings = Settings()
