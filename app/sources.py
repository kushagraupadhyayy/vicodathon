from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import feedparser


@dataclass(frozen=True)
class CandidateTopic:
    title: str
    summary: str
    source_urls: list[str]
    source_name: str

    @property
    def fingerprint(self) -> str:
        clean_title = re.sub(r"\s+", " ", self.title.lower()).strip()
        clean_summary = re.sub(r"\s+", " ", self.summary.lower()).strip()[:200]
        normalized = f"{clean_title}::{clean_summary}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


HN_TOPSTORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
ARXIV_URL = "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CR&start=0&max_results=15&sortBy=submittedDate&sortOrder=descending"
RSS_FEEDS = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("MIT Tech Review AI", "https://www.technologyreview.com/feed/"),
]
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) VicodathonPersonaBot/1.0"


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def _fetch_url(url: str, headers: dict[str, str] | None = None) -> bytes:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    request = Request(url, headers=req_headers)
    with urlopen(request, timeout=15) as response:
        return response.read()


def _fetch_json(url: str) -> object:
    raw = _fetch_url(url)
    return json.loads(raw.decode("utf-8"))


def fetch_hn_candidates(limit: int = 15) -> list[CandidateTopic]:
    candidates: list[CandidateTopic] = []
    try:
        top_story_ids = _fetch_json(HN_TOPSTORIES_URL)[:limit]
        for item_id in top_story_ids:
            item = _fetch_json(HN_ITEM_URL.format(item_id=item_id))
            if not isinstance(item, dict):
                continue
            title = _clean_text(str(item.get("title") or ""))
            if not title:
                continue
            url = str(item.get("url") or HN_ITEM_URL.format(item_id=item_id))
            text = _clean_text(str(item.get("text") or ""))
            candidates.append(
                CandidateTopic(
                    title=title,
                    summary=text or title,
                    source_urls=[url],
                    source_name="Hacker News",
                )
            )
    except Exception:
        return candidates
    return candidates


def fetch_arxiv_candidates(limit: int = 15) -> list[CandidateTopic]:
    candidates: list[CandidateTopic] = []
    try:
        raw_xml = _fetch_url(ARXIV_URL)
        root = ElementTree.fromstring(raw_xml)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", namespace)[:limit]:
            raw_title = entry.findtext("atom:title", default="", namespaces=namespace) or ""
            raw_summary = entry.findtext("atom:summary", default="", namespaces=namespace) or ""
            title = _clean_text(raw_title)
            summary = _clean_text(raw_summary)
            link = entry.find("atom:link[@rel='alternate']", namespace)
            url = link.attrib.get("href", "") if link is not None else ""
            if title:
                candidates.append(
                    CandidateTopic(
                        title=title,
                        summary=summary or title,
                        source_urls=[url] if url else [],
                        source_name="arXiv",
                    )
                )
    except Exception:
        return candidates
    return candidates


def fetch_rss_candidates() -> list[CandidateTopic]:
    candidates: list[CandidateTopic] = []
    for source_name, feed_url in RSS_FEEDS:
        try:
            raw_xml = _fetch_url(feed_url)
            parsed = feedparser.parse(raw_xml)
            for entry in parsed.entries[:10]:
                title = _clean_text(getattr(entry, "title", ""))
                summary = _clean_text(getattr(entry, "summary", ""))
                link = getattr(entry, "link", "").strip()
                if title:
                    candidates.append(
                        CandidateTopic(
                            title=title,
                            summary=summary or title,
                            source_urls=[link] if link else [],
                            source_name=source_name,
                        )
                    )
        except Exception:
            continue
    return candidates


def fetch_newsapi_candidates(api_key: str | None, limit: int = 10) -> list[CandidateTopic]:
    if not api_key:
        return []
    candidates: list[CandidateTopic] = []
    query = urlencode(
        {
            "q": "AI OR security OR vulnerability OR LLM",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": str(limit),
            "apiKey": api_key,
        }
    )
    try:
        payload = _fetch_json(f"{NEWSAPI_ENDPOINT}?{query}")
        if isinstance(payload, dict):
            for article in payload.get("articles", [])[:limit]:
                title = _clean_text(str(article.get("title") or ""))
                summary = _clean_text(str(article.get("description") or article.get("content") or title))
                url = str(article.get("url") or "").strip()
                if title:
                    candidates.append(
                        CandidateTopic(
                            title=title,
                            summary=summary or title,
                            source_urls=[url] if url else [],
                            source_name="NewsAPI",
                        )
                    )
    except Exception:
        return candidates
    return candidates


def discover_candidates(newsapi_key: str | None = None) -> list[CandidateTopic]:
    candidates = (
        fetch_hn_candidates()
        + fetch_arxiv_candidates()
        + fetch_rss_candidates()
        + fetch_newsapi_candidates(newsapi_key)
    )
    return _deduplicate(candidates)


def _deduplicate(candidates: Iterable[CandidateTopic]) -> list[CandidateTopic]:
    seen: set[str] = set()
    unique: list[CandidateTopic] = []
    for candidate in candidates:
        if candidate.fingerprint in seen:
            continue
        seen.add(candidate.fingerprint)
        unique.append(candidate)
    return unique

