"""
F004 验收：文章采集与入库 API（单条/批量写入，与来源关联）。
直接运行: python -m tests.test_articles_api
"""
import os
import sys
import tempfile
if "DATABASE_URL" not in os.environ:
    _fd, _path = tempfile.mkstemp(suffix=".db")
    os.close(_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{_path}"

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


def test_articles_create_and_list():
    """单条/批量入库，文章包含标题、原文链接、来源、日期，可与来源关联。"""
    init_db()
    with TestClient(app) as client:
        # 1. 先建一个来源，用于按来源 ID 录入
        r = client.post(
            "/sources",
            json={"name": "测试来源", "type_or_kind": "rss", "url_or_config": "https://a.com/feed"},
        )
        assert r.status_code == 201
        source_id = r.json()["id"]

        # 2. 列表为空
        r = client.get("/articles")
        assert r.status_code == 200
        assert r.json() == []

        # 3. 单条入库：标题、原文链接、来源、日期
        pub_at = "2026-02-13T10:00:00+00:00"
        r = client.post(
            "/articles",
            json={
                "title": "热点文章一",
                "url": "https://example.com/article/1",
                "source_id": source_id,
                "published_at": pub_at,
                "summary": "摘要一",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "热点文章一"
        assert data["url"] == "https://example.com/article/1"
        assert data["source_id"] == source_id
        assert data["published_at"] is not None and "2026-02-13" in data["published_at"]
        assert "id" in data and data["id"] >= 1
        assert data.get("created_at") is not None

        # 4. 列表有一条，且字段完整
        r = client.get("/articles")
        assert r.status_code == 200
        articles = r.json()
        assert len(articles) == 1
        a = articles[0]
        assert a["title"] == "热点文章一"
        assert a["url"] == "https://example.com/article/1"
        assert a["source_id"] == source_id
        assert a["published_at"] is not None and "2026-02-13" in a["published_at"]

        # 5. 批量入库
        r = client.post(
            "/articles/batch",
            json={
                "articles": [
                    {
                        "title": "批量一",
                        "url": "https://example.com/batch/1",
                        "source_id": source_id,
                        "published_at": "2026-02-12T09:00:00+00:00",
                    },
                    {
                        "title": "批量二",
                        "url": "https://example.com/batch/2",
                        "source_id": None,
                        "published_at": None,
                    },
                ]
            },
        )
        assert r.status_code == 201
        batch = r.json()
        assert len(batch) == 2
        assert batch[0]["title"] == "批量一" and batch[1]["title"] == "批量二"

        # 6. 列表共三条
        r = client.get("/articles")
        assert r.status_code == 200
        assert len(r.json()) == 3

        # 7. source_id 不存在时 404
        r = client.post(
            "/articles",
            json={
                "title": "无效来源",
                "url": "https://x.com/1",
                "source_id": 99999,
            },
        )
        assert r.status_code == 404


if __name__ == "__main__":
    test_articles_create_and_list()
    print("F004 文章采集与入库 验收通过")
    sys.exit(0)
