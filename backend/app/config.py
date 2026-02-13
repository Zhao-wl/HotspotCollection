"""
应用配置：从环境变量加载，不硬编码密钥。
"""
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


# 使用基于本文件位置的 .env 绝对路径，确保无论从项目根或 backend 启动都能加载
_env_file = Path(__file__).resolve().parent.parent / ".env"


def _load_env_file(path: Path) -> None:
    """手动解析 .env 并写入 os.environ（不覆盖已存在变量），不依赖 python-dotenv。"""
    if not path.exists():
        return
    try:
        with open(path, "r", encoding="utf-8-sig") as f:  # utf-8-sig 去除 BOM
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value and (key not in os.environ or not os.environ[key].strip()):
                    os.environ[key] = value
    except Exception:
        pass


_load_env_file(_env_file)

# 若已安装 python-dotenv 可选用其加载（与上面手动加载二选一即可，此处作补充）
try:
    from dotenv import load_dotenv
    if _env_file.exists():
        load_dotenv(_env_file, override=False)
except ImportError:
    pass


class Settings(BaseSettings):
    """硅基流动 API（用于 LangExtract / 关键词提取）。"""

    siliconflow_api_key: str = Field(
        "", validation_alias="SILICONFLOW_API_KEY"
    )
    siliconflow_base_url: str = Field(
        "https://api.siliconflow.cn/v1", validation_alias="SILICONFLOW_BASE_URL"
    )
    siliconflow_model: str = Field(
        "Qwen/Qwen3-8B", validation_alias="SILICONFLOW_MODEL"
    )

    class Config:
        env_prefix = "SILICONFLOW_"
        # 不传 env_file，仅从 os.environ 读取（已由 _load_env_file 从 .env 写入）
        extra = "ignore"


settings = Settings()
