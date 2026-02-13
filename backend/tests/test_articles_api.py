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


def test_articles_list_filter_and_pagination():
    """F006 验收：文章列表支持按日期、标签、来源筛选，分页；返回标题、标签、来源、链接、日期。"""
    if "DATABASE_URL" not in os.environ:
        _fd, _path = tempfile.mkstemp(suffix=".db")
        os.close(_fd)
        os.environ["DATABASE_URL"] = f"sqlite:///{_path}"
    init_db()
    with TestClient(app) as client:
        # 准备：两个来源、若干文章（不同日期）、部分带标签
        r = client.post(
            "/sources",
            json={"name": "来源A", "type_or_kind": "rss", "url_or_config": "https://a.com"},
        )
        assert r.status_code == 201
        source_a = r.json()["id"]
        r = client.post(
            "/sources",
            json={"name": "来源B", "type_or_kind": "api", "url_or_config": "https://b.com"},
        )
        assert r.status_code == 201
        source_b = r.json()["id"]

        r = client.post(
            "/articles/batch",
            json={
                "articles": [
                    {"title": "文章1", "url": "https://ex.com/1", "source_id": source_a, "published_at": "2026-02-10T12:00:00"},
                    {"title": "文章2", "url": "https://ex.com/2", "source_id": source_a, "published_at": "2026-02-12T12:00:00"},
                    {"title": "文章3", "url": "https://ex.com/3", "source_id": source_b, "published_at": "2026-02-14T12:00:00"},
                    {"title": "文章4", "url": "https://ex.com/4", "source_id": source_a, "published_at": "2026-02-15T12:00:00"},
                ]
            },
        )
        assert r.status_code == 201
        ids = [a["id"] for a in r.json()]
        # 给文章2、文章3 提取关键词（会创建标签并关联）
        client.post(f"/articles/{ids[1]}/extract-keywords")  # 文章2
        client.post(f"/articles/{ids[2]}/extract-keywords")  # 文章3
        # 获取一个 tag_id 用于筛选
        r_tags = client.get("/tags")
        tag_id = r_tags.json()[0]["id"] if r_tags.json() else None

        # 1. 列表返回字段包含：标题、标签、来源（source_name）、原文链接、日期
        r = client.get("/articles")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 4
        item = next((x for x in data if x["title"] == "文章2"), data[0])
        assert "title" in item and "url" in item and "published_at" in item
        assert "source_id" in item and "source_name" in item
        assert "tags" in item and isinstance(item["tags"], list)

        # 2. 按来源筛选
        r = client.get(f"/articles?source_id={source_b}")
        assert r.status_code == 200
        assert all(a["source_id"] == source_b for a in r.json())

        # 3. 按日期范围筛选
        r = client.get("/articles?date_from=2026-02-12&date_to=2026-02-14")
        assert r.status_code == 200
        titles = [a["title"] for a in r.json()]
        assert "文章2" in titles and "文章3" in titles
        assert "文章1" not in titles and "文章4" not in titles

        # 4. 按标签筛选（若有标签）
        if tag_id is not None:
            r = client.get(f"/articles?tag_id={tag_id}")
            assert r.status_code == 200
            assert len(r.json()) >= 1

        # 5. 分页：limit / offset
        r = client.get("/articles?limit=2&offset=0")
        assert r.status_code == 200
        assert len(r.json()) <= 2
        r2 = client.get("/articles?limit=2&offset=2")
        assert r.status_code == 200
        assert len(r2.json()) <= 2
        # 两页结果不应重复
        ids_page1 = {a["id"] for a in r.json()}
        ids_page2 = {a["id"] for a in r2.json()}
        assert ids_page1.isdisjoint(ids_page2)


if __name__ == "__main__":
    test_articles_create_and_list()
    print("F004 文章采集与入库 验收通过")
    test_articles_list_filter_and_pagination()
    print("F006 文章展示 API 验收通过")
    sys.exit(0)
