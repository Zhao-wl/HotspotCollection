"""
F012 验收：采集后自动对获取到的文章进行 LangExtract 关键词提取。
- 单来源采集入库的新文章在入库后自动提取关键词并关联；
- 未配置 API Key 或提取失败时，新文章仍正常入库，仅无关键词。
"""
import os
import sys
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

if "DATABASE_URL" not in os.environ:
    _fd, _path = tempfile.mkstemp(suffix=".db")
    os.close(_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{_path}"

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


def test_collect_then_auto_extract_keywords():
    """单来源采集后，新文章自动关联 LangExtract 提取的关键词。"""
    init_db()
    with TestClient(app) as client:
        # 1. 创建 rss 来源
        r = client.post(
            "/sources",
            json={"name": "测试RSS", "type_or_kind": "rss", "url_or_config": "https://example.com/feed.xml"},
        )
        assert r.status_code == 201
        source_id = r.json()["id"]

        # 2. Mock RSS 拉取返回一条文章，Mock 关键词提取返回两个关键词
        fake_items = [
            {
                "title": "人工智能新进展",
                "url": "https://example.com/ai-news",
                "published_at": datetime.now(timezone.utc),
                "summary": "深度学习与自然语言处理。",
            }
        ]
        with patch("app.services.collector.fetch_rss", return_value=fake_items), patch(
            "app.services.article_keywords.extract_keywords", return_value=["人工智能", "深度学习"]
        ):
            r = client.post(f"/collect/run/{source_id}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert data.get("articles_added") == 1

        # 3. 新文章应已关联关键词
        r = client.get("/articles")
        assert r.status_code == 200
        articles = r.json()
        assert len(articles) >= 1
        new_one = next((a for a in articles if a.get("url") == "https://example.com/ai-news"), None)
        assert new_one is not None
        tags = new_one.get("tags") or []
        names = {t["name"] for t in tags}
        assert "人工智能" in names
        assert "深度学习" in names


def test_collect_without_api_key_still_inserts_articles():
    """未配置 API Key 或提取失败时，新文章仍正常入库，仅无关键词。"""
    init_db()
    with TestClient(app) as client:
        r = client.post(
            "/sources",
            json={"name": "测试RSS2", "type_or_kind": "rss", "url_or_config": "https://other.com/feed.xml"},
        )
        assert r.status_code == 201
        source_id = r.json()["id"]

        fake_items = [
            {
                "title": "无关键词文章",
                "url": "https://other.com/no-kw",
                "published_at": datetime.now(timezone.utc),
                "summary": "摘要",
            }
            ]
        # 不 mock extract_keywords，无 API Key 时返回 []，采集仍应成功
        with patch("app.services.collector.fetch_rss", return_value=fake_items):
            r = client.post(f"/collect/run/{source_id}")
        assert r.status_code == 200
        assert r.json().get("ok") is True
        assert r.json().get("articles_added") == 1

        r = client.get("/articles")
        new_one = next((a for a in r.json() if a.get("url") == "https://other.com/no-kw"), None)
        assert new_one is not None
        assert (new_one.get("tags") or []) == []  # 无关键词


if __name__ == "__main__":
    test_collect_then_auto_extract_keywords()
    test_collect_without_api_key_still_inserts_articles()
    print("F012 采集后自动关键词提取 验收通过")
    sys.exit(0)
