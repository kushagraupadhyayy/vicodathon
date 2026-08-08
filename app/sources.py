from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import urlopen
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
        normalized = re.sub(r"\s+", " ", f"{self.title} {self.summary}".lower()).strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


HN_TOPSTORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
ARXIV_URL = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
RSS_FEEDS = [
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
]
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"


def _fetch_json(url: str) -> object:
    with urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_hn_candidates(limit: int = 10) -> list[CandidateTopic]:
    candidates: list[CandidateTopic] = []
    try:
        top_story_ids = _fetch_json(HN_TOPSTORIES_URL)[:limit]
        for item_id in top_story_ids:
            item = _fetch_json(HN_ITEM_URL.format(item_id=item_id))
            title = str(item.get("title", ""))
            if not title:
                continue
            url = str(item.get("url") or HN_ITEM_URL.format(item_id=item_id))
            text = str(item.get("text") or "")
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


def fetch_arxiv_candidates(limit: int = 10) -> list[CandidateTopic]:
    candidates: list[CandidateTopic] = []
    try:
        with urlopen(ARXIV_URL, timeout=15) as response:
            root = ElementTree.fromstring(response.read())
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", namespace)[:limit]:
            title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=namespace) or "").strip()
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
    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:10]:
                title = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "").strip()
                link = getattr(entry, "link", "").strip()
                if title:
                    candidates.append(
                        CandidateTopic(
                            title=title,
                            summary=summary or title,
                            source_urls=[link] if link else [],
                            source_name=feed_url,
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
            "q": 'AI OR machine learning OR model OR security',
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": str(limit),
            "apiKey": api_key,
        }
    )
    try:
        with urlopen(f"{NEWSAPI_ENDPOINT}?{query}", timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for article in payload.get("articles", [])[:limit]:
            title = str(article.get("title") or "").strip()
            summary = str(article.get("description") or article.get("content") or title).strip()
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
    candidates = fetch_hn_candidates() + fetch_arxiv_candidates() + fetch_rss_candidates() + fetch_newsapi_candidates(newsapi_key)
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
