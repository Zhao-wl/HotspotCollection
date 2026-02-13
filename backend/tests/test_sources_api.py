"""
F003 验收：来源配置 CRUD API。
直接运行: python -m tests.test_sources_api
可选: DATABASE_URL=... 指定数据库（未设置时使用临时文件，避免污染 data.db）。
"""
import os
import sys
import tempfile

# 测试时使用临时文件 DB，避免 :memory: 多连接不同库的问题；须在导入 app 前设置
if "DATABASE_URL" not in os.environ:
    _fd, _path = tempfile.mkstemp(suffix=".db")
    os.close(_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{_path}"

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


def test_sources_crud():
    """来源 CRUD + 持久化到 SQLite。"""
    init_db()  # 确保表存在（与 app lifespan 一致）
    with TestClient(app) as client:
        # 1. 列表为空
        r = client.get("/sources")
        assert r.status_code == 200
        assert r.json() == []

        # 2. 创建
        r = client.post(
            "/sources",
            json={
                "name": "RSS 示例",
                "type_or_kind": "rss",
                "url_or_config": "https://example.com/feed.xml",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "RSS 示例"
        assert data["type_or_kind"] == "rss"
        assert data["url_or_config"] == "https://example.com/feed.xml"
        assert "id" in data and data["id"] >= 1
        sid = data["id"]

        # 3. 列表有一条
        r = client.get("/sources")
        assert r.status_code == 200
        assert len(r.json()) == 1

        # 4. 获取单条
        r = client.get(f"/sources/{sid}")
        assert r.status_code == 200
        assert r.json()["name"] == "RSS 示例"

        # 5. 更新
        r = client.patch(f"/sources/{sid}", json={"name": "RSS 更新"})
        assert r.status_code == 200
        assert r.json()["name"] == "RSS 更新"

        # 6. 删除
        r = client.delete(f"/sources/{sid}")
        assert r.status_code == 204

        # 7. 列表又为空
        r = client.get("/sources")
        assert r.status_code == 200
        assert r.json() == []

        # 8. 404
        r = client.get("/sources/999")
        assert r.status_code == 404


if __name__ == "__main__":
    test_sources_crud()
    print("F003 CRUD + 持久化 验收通过")
    sys.exit(0)
