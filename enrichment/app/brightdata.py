"""Bright Data client: SERP API (search) + Web Unlocker (scrape).

Both go through the same endpoint (https://api.brightdata.com/request); the
`zone` parameter selects which product handles the request.
"""

import asyncio
import json
import re
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from . import cache
from .config import (
    BRIGHTDATA_API_TOKEN,
    BRIGHTDATA_ENDPOINT,
    BRIGHTDATA_SERP_ZONE,
    BRIGHTDATA_UNLOCKER_ZONE,
    HAS_BRIGHTDATA,
)

TIMEOUT = httpx.Timeout(60.0, connect=15.0)


class BrightDataError(RuntimeError):
    pass


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}",
        "Content-Type": "application/json",
    }


async def _request(zone: str, url: str, fmt: str) -> httpx.Response:
    if not HAS_BRIGHTDATA:
        raise BrightDataError(
            "BRIGHTDATA_API_TOKEN is not set. Copy .env.example to .env and fill it in."
        )
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            BRIGHTDATA_ENDPOINT,
            headers=_headers(),
            json={"zone": zone, "url": url, "format": fmt},
        )
    if resp.status_code >= 400:
        raise BrightDataError(f"Bright Data {resp.status_code}: {resp.text[:300]}")
    return resp


def html_to_text(html: str, max_chars: int = 12000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()[:max_chars]


async def search(query: str, num: int = 10, use_cache: bool = True) -> list[dict]:
    """SERP API search. Returns [{title, url, snippet}]."""
    params = {"query": query, "num": num}
    if use_cache:
        hit = cache.get("serp", params)
        if hit:
            return hit["payload"]

    # NOTE: Bright Data strips a `num` query param from Google URLs, so we slice
    # client-side instead of asking Google for a specific result count.
    target = f"https://www.google.com/search?q={quote_plus(query)}"
    resp = await _request(BRIGHTDATA_SERP_ZONE, target, "json")

    results: list[dict] = []
    for item in _extract_organic(resp)[:num]:
        url = item.get("link") or item.get("url", "")
        if not _is_usable_url(url):
            continue
        results.append(
            {
                "title": item.get("title", ""),
                "url": url,
                "snippet": item.get("description") or item.get("snippet", ""),
            }
        )

    if not results:
        # Fallback: some zones return raw HTML even with format=json.
        results = _parse_serp_html(_body_html(resp), num)

    cache.put("serp", params, results)
    return results


def _is_usable_url(url: str) -> bool:
    """Reject relative links, Google redirect wrappers, and binary documents.

    Google sometimes returns `/goto?url=<opaque>` redirect links instead of the
    real destination; those are unciteable and unscrapeable, so drop them rather
    than surface them to a portal as a "source".
    """
    if not url or not url.lower().startswith(("http://", "https://")):
        return False
    lowered = url.lower()
    if "google.com/url?" in lowered or "/goto?url=" in lowered:
        return False
    if lowered.split("?")[0].endswith((".pdf", ".doc", ".docx", ".zip", ".ppt", ".pptx")):
        return False
    return True


def _looks_binary(text: str) -> bool:
    """True when decoded content is not readable prose (PDF bytes, gzip, etc.)."""
    if not text:
        return True
    sample = text[:2000]
    bad = sum(1 for ch in sample if ch == "�" or (ord(ch) < 32 and ch not in "\r\n\t"))
    return (bad / max(len(sample), 1)) > 0.05


def _extract_organic(resp: httpx.Response) -> list[dict]:
    """Pull the organic results list out of a SERP API response.

    Bright Data wraps the payload as {status_code, headers, body} where `body`
    is a JSON *string* holding {general, input, organic, navigation}. Older/other
    zone configs return the parsed object directly, so handle both.
    """
    try:
        data = resp.json()
    except Exception:
        return []

    candidates = [data]
    body = data.get("body") if isinstance(data, dict) else None
    if isinstance(body, str):
        try:
            candidates.append(json.loads(body))
        except Exception:
            pass
    elif isinstance(body, dict):
        candidates.append(body)

    for cand in candidates:
        if isinstance(cand, dict) and isinstance(cand.get("organic"), list):
            return cand["organic"]
    return []


def _body_html(resp: httpx.Response) -> str:
    """Return the page HTML, unwrapping the {status_code, headers, body} envelope."""
    text = resp.text
    stripped = text.lstrip()
    if not stripped.startswith("{"):
        return text
    try:
        data = resp.json()
    except Exception:
        return text
    if isinstance(data, dict) and isinstance(data.get("body"), str):
        return data["body"]
    return text


def _parse_serp_html(html: str, num: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    seen = set()
    for a in soup.select("a[href^='http']"):
        href = a.get("href", "")
        if "google.com" in href or href in seen:
            continue
        title = a.get_text(strip=True)
        if len(title) < 15:
            continue
        seen.add(href)
        out.append({"title": title, "url": href, "snippet": ""})
        if len(out) >= num:
            break
    return out


async def scrape(url: str, use_cache: bool = True) -> Optional[dict]:
    """Web Unlocker scrape. Returns {url, text, chars} or None on failure."""
    if not _is_usable_url(url):
        return None

    params = {"url": url}
    if use_cache:
        hit = cache.get("scrape", params)
        if hit:
            return hit["payload"]

    try:
        resp = await _request(BRIGHTDATA_UNLOCKER_ZONE, url, "raw")
    except BrightDataError:
        return None

    raw = _body_html(resp)
    if _looks_binary(raw):
        return None

    text = html_to_text(raw)
    if len(text) < 200 or _looks_binary(text):
        return None

    payload = {"url": url, "text": text, "chars": len(text)}
    cache.put("scrape", params, payload)
    return payload


async def search_and_scrape(
    query: str, limit: int = 3, use_cache: bool = True
) -> list[dict]:
    """Search, then pull full text for the top N results. The workhorse call.

    Scrapes run concurrently — serial scraping is the main latency cost here, and
    prefetch would otherwise take many minutes.
    """
    hits = await search(query, num=max(limit * 2, 6), use_cache=use_cache)

    # Over-fetch slightly so blocked pages don't starve the result set.
    candidates = [h for h in hits if h.get("url")][: limit + 2]
    scraped = await asyncio.gather(
        *(scrape(h["url"], use_cache=use_cache) for h in candidates),
        return_exceptions=True,
    )

    docs: list[dict] = []
    for hit, doc in zip(candidates, scraped):
        if len(docs) >= limit:
            break
        if isinstance(doc, Exception) or not doc:
            continue
        docs.append({**doc, "title": hit.get("title", ""), "snippet": hit.get("snippet", "")})
    # Nothing scraped cleanly — fall back to snippets so callers still get cited text.
    if not docs:
        docs = [
            {
                "url": h["url"],
                "title": h.get("title", ""),
                "text": h.get("snippet", ""),
                "chars": len(h.get("snippet", "")),
                "snippet": h.get("snippet", ""),
            }
            for h in hits[:limit]
            if h.get("url") and h.get("snippet")
        ]
    return docs
