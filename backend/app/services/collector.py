"""
自动采集服务：从配置的 RSS/API 来源拉取文章并入库，供长线后台任务调用。
"""
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.models import Article, Source

# 已知的 RSS 纠正：博客首页或失效 URL -> 实际可用的 feed URL（避免 403/404）
_RSS_URL_CORRECTIONS: dict[str, str] = {
    "https://openai.com/blog": "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/feed.xml": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
}


def _parse_rss_date(entry: Any) -> datetime | None:
    """将 feedparser 的 time 转为 datetime。"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            from time import struct_time
            st: struct_time = entry.published_parsed
            return datetime(*st[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            from time import struct_time
            st = entry.updated_parsed
            return datetime(*st[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    return None


def fetch_rss(feed_url: str, timeout: float = 15.0) -> list[dict[str, Any]]:
    """
    拉取并解析 RSS/Atom，返回可入库的条目列表。
    每条: title, url, published_at (datetime | None), summary (str | None)。
    无 link 的条目会跳过。使用 httpx + 浏览器风格 User-Agent 以兼容 RSSHub 等反爬源。
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(feed_url, headers=headers)
            r.raise_for_status()
            resp = feedparser.parse(r.text)
    except Exception:
        raise
    items = []
    for entry in getattr(resp, "entries", []) or []:
        link = (entry.get("link") or "").strip()
        if not link:
            continue
        title = (entry.get("title") or "").strip() or "(无标题)"
        if len(title) > 512:
            title = title[:509] + "..."
        summary = None
        if entry.get("summary"):
            summary = (entry.get("summary") or "").strip() or None
        published_at = _parse_rss_date(entry)
        items.append({
            "title": title,
            "url": link,
            "published_at": published_at,
            "summary": summary,
        })
    return items


def fetch_api(api_url: str, timeout: float = 15.0) -> list[dict[str, Any]]:
    """
    从 API URL GET JSON，期望返回数组，每项含 title、url，可选 published_at、summary。
    返回格式与 fetch_rss 一致。
    """
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(api_url)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    items = []
    for row in data:
        if not isinstance(row, dict):
            continue
        url = (row.get("url") or row.get("link") or "").strip()
        if not url:
            continue
        title = (row.get("title") or "").strip() or "(无标题)"
        if len(title) > 512:
            title = title[:509] + "..."
        summary = row.get("summary")
        if summary is not None:
            summary = (str(summary)).strip() or None
        published_at = None
        if row.get("published_at") or row.get("published") or row.get("date"):
            raw = row.get("published_at") or row.get("published") or row.get("date")
            if isinstance(raw, (int, float)):
                published_at = datetime.fromtimestamp(raw, tz=timezone.utc)
            elif isinstance(raw, str):
                try:
                    published_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass
        items.append({
            "title": title,
            "url": url,
            "published_at": published_at,
            "summary": summary,
        })
    return items


def _dedupe_and_insert(db: Session, source_id: int, items: list[dict[str, Any]]) -> int:
    """按 (source_id, url) 去重，只插入新文章；返回本次新增数量。"""
    added = 0
    for item in items:
        exists = (
            db.query(Article)
            .filter(Article.source_id == source_id, Article.url == item["url"])
            .first()
        )
        if exists:
            continue
        article = Article(
            title=item["title"],
            url=item["url"],
            source_id=source_id,
            published_at=item.get("published_at"),
            summary=item.get("summary"),
        )
        db.add(article)
        added += 1
    return added


def run_collection(db: Session) -> dict[str, Any]:
    """
    对全部配置了 URL 的 rss/api 来源执行一次采集，去重后入库。
    返回: { "sources_ok": int, "sources_fail": int, "articles_added": int, "errors": list[str] }
    """
    sources = db.query(Source).filter(
        Source.type_or_kind.in_(["rss", "api"]),
        Source.url_or_config.isnot(None),
        Source.url_or_config != "",
    ).all()
    sources_ok = 0
    sources_fail = 0
    articles_added = 0
    errors: list[str] = []

    for src in sources:
        url = (src.url_or_config or "").strip()
        if not url:
            continue
        try:
            if (src.type_or_kind or "").lower() == "rss":
                feed_url = _RSS_URL_CORRECTIONS.get(url.rstrip("/"), url)
                items = fetch_rss(feed_url)
            else:
                items = fetch_api(url)
            n = _dedupe_and_insert(db, src.id, items)
            db.commit()
            articles_added += n
            sources_ok += 1
        except Exception as e:
            db.rollback()
            sources_fail += 1
            errors.append(f"source id={src.id} ({src.name}): {e!s}")

    return {
        "sources_ok": sources_ok,
        "sources_fail": sources_fail,
        "articles_added": articles_added,
        "errors": errors,
    }
