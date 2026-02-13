"""
F005 验收：关键词提取与聚合。
- 集成 langextract，可对指定文本或文章进行关键词提取；
- LLM 使用硅基流动 API（环境变量配置，不硬编码密钥）；
- 提取的关键词关联到文章并支持按关键词聚合查询。
测试中 mock 关键词提取结果，不依赖真实 API Key。
"""
import os
import sys
import tempfile
from unittest.mock import patch

if "DATABASE_URL" not in os.environ:
    _fd, _path = tempfile.mkstemp(suffix=".db")
    os.close(_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{_path}"

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


def test_keyword_extract_and_aggregation():
    """关键词提取接口、关联到文章、按标签筛选列表；GET /tags 可用。"""
    init_db()
    with TestClient(app) as client:
        # 1. 准备：来源 + 一篇文章（有标题与摘要）
        r = client.post(
            "/sources",
            json={"name": "测试来源", "type_or_kind": "rss", "url_or_config": "https://a.com/feed"},
        )
        assert r.status_code == 201
        source_id = r.json()["id"]
        r = client.post(
            "/articles",
            json={
                "title": "人工智能与机器学习发展",
                "url": "https://example.com/ai",
                "source_id": source_id,
                "summary": "摘要：深度学习与自然语言处理。",
            },
        )
        assert r.status_code == 201
        article_id = r.json()["id"]

        # 2. Mock 关键词提取，不依赖硅基流动 API（patch 调用方使用的引用）
        with patch("app.services.article_keywords.extract_keywords", return_value=["人工智能", "机器学习"]):
            r = client.post(f"/articles/{article_id}/extract-keywords")
        assert r.status_code == 200
        tags = r.json()
        assert len(tags) == 2
        names = {t["name"] for t in tags}
        assert names == {"人工智能", "机器学习"}
        tag_ids = [t["id"] for t in tags]

        # 3. 标签列表 API
        r = client.get("/tags")
        assert r.status_code == 200
        all_tags = r.json()
        assert len(all_tags) >= 2
        assert names.issubset({t["name"] for t in all_tags})

        # 4. 按关键词聚合查询：GET /articles?tag_id=...
        r = client.get("/articles", params={"tag_id": tag_ids[0]})
        assert r.status_code == 200
        articles = r.json()
        assert len(articles) >= 1
        ids = [a["id"] for a in articles]
        assert article_id in ids

        # 5. 文章不存在时 404
        r = client.post("/articles/99999/extract-keywords")
        assert r.status_code == 404


def test_extract_keywords_without_api_key_returns_empty():
    """未配置 API Key 时，提取接口仍可调用，返回空标签列表（不报错）。"""
    init_db()
    with TestClient(app) as client:
        r = client.post("/sources", json={"name": "S", "type_or_kind": "manual", "url_or_config": None})
        assert r.status_code == 201
        r = client.post("/articles", json={"title": "T", "url": "https://x.com/1", "source_id": r.json()["id"]})
        assert r.status_code == 201
        aid = r.json()["id"]
        # 未 mock，且无 API Key 时 extract_keywords 返回 []
        r = client.post(f"/articles/{aid}/extract-keywords")
        assert r.status_code == 200
        assert r.json() == []


if __name__ == "__main__":
    test_keyword_extract_and_aggregation()
    test_extract_keywords_without_api_key_returns_empty()
    print("F005 关键词提取与聚合 验收通过")
    sys.exit(0)
