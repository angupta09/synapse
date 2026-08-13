"""Enrichment pipelines — the three products Team B ships to the rest of Synapse."""

import asyncio

from . import brightdata, cache, safety, summarize


def _sources(docs: list[dict]) -> list[dict]:
    return [{"url": d.get("url", ""), "title": d.get("title", "")} for d in docs if d.get("url")]


async def _gather_queries(queries: list[str], limit: int, use_cache: bool) -> list[dict]:
    """Run several searches concurrently and merge, de-duplicated by URL."""
    batches = await asyncio.gather(
        *(brightdata.search_and_scrape(q, limit=limit, use_cache=use_cache) for q in queries),
        return_exceptions=True,
    )
    docs: list[dict] = []
    seen: set[str] = set()
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for doc in batch:
            if doc["url"] not in seen:
                seen.add(doc["url"])
                docs.append(doc)
    return docs


# --- Patient Portal -------------------------------------------------------

PATIENT_TRUSTED_SITES = (
    "site:cancer.gov OR site:nih.gov OR site:medlineplus.gov OR site:clinicaltrials.gov "
    "OR site:rarediseases.org OR site:mayoclinic.org"
)


async def patient_summary(
    condition_id: str, treatment_id: str, condition_name: str, treatment_name: str, refresh: bool = False
) -> dict:
    """Vetted, plain-language, safety-gated summary for the Patient Portal."""
    params = {"condition_id": condition_id, "treatment_id": treatment_id}
    if not refresh:
        hit = cache.get("patient_summary", params)
        if hit:
            return {**hit["payload"], "fetched_at": hit["fetched_at"], "cached": True}

    # Trusted-site filter first; if it returns nothing (common for newer drugs),
    # fall back to an unrestricted query rather than shipping an empty summary.
    docs = await brightdata.search_and_scrape(
        f"{treatment_name} {condition_name} treatment overview {PATIENT_TRUSTED_SITES}",
        limit=3,
        use_cache=not refresh,
    )
    if not docs:
        docs = await brightdata.search_and_scrape(
            f"what is {treatment_name} used for {condition_name} patient information",
            limit=3,
            use_cache=not refresh,
        )

    draft = summarize.patient_summary(treatment_name, condition_name, docs)
    verdict = safety.gate(draft["content"], docs)

    payload = {
        "condition_id": condition_id,
        "treatment_id": treatment_id,
        "condition_name": condition_name,
        "treatment_name": treatment_name,
        "content": verdict["content"],
        "disclaimer": verdict["disclaimer"],
        "safety": {
            "passed": verdict["passed"],
            "checks_run": verdict["checks_run"],
            "violations": verdict["violations"],
        },
        "summarization_mode": draft["mode"],
        "sources": _sources(docs),
        "source_url": (_sources(docs)[0]["url"] if _sources(docs) else None),
    }
    fetched_at = cache.put("patient_summary", params, payload)
    return {**payload, "fetched_at": fetched_at, "cached": False}


# --- Trial Design Portal --------------------------------------------------


async def trial_context(nct_id: str, trial_title: str = "", refresh: bool = False) -> dict:
    """Sponsor / investigator / press context surrounding a specific trial."""
    params = {"nct_id": nct_id}
    if not refresh:
        hit = cache.get("trial_context", params)
        if hit:
            return {**hit["payload"], "fetched_at": hit["fetched_at"], "cached": True}

    queries = [
        f'"{nct_id}" clinical trial sponsor results',
        f'"{nct_id}" trial terminated OR discontinued OR halted news',
    ]
    if trial_title:
        queries.append(f'"{trial_title}" trial press release OR conference abstract')

    docs = await _gather_queries(queries, limit=2, use_cache=not refresh)
    summary = summarize.trial_context(nct_id, docs)
    payload = {
        "nct_id": nct_id,
        "trial_title": trial_title,
        "content": summary["content"],
        "summarization_mode": summary["mode"],
        "has_context": summary["ok"],
        "sources": _sources(docs),
        "source_url": (_sources(docs)[0]["url"] if _sources(docs) else None),
        "raw_excerpts": [
            {"url": d["url"], "title": d.get("title", ""), "excerpt": d.get("text", "")[:800]}
            for d in docs
        ],
    }
    fetched_at = cache.put("trial_context", params, payload)
    return {**payload, "fetched_at": fetched_at, "cached": False}


# --- R&D Portal -----------------------------------------------------------


async def competitive_signal(target_id: str, target_name: str = "", refresh: bool = False) -> dict:
    """Competitive-intelligence items tied to a target/mechanism, for Portal 3."""
    params = {"target_id": target_id}
    if not refresh:
        hit = cache.get("competitive_signal", params)
        if hit:
            return {**hit["payload"], "fetched_at": hit["fetched_at"], "cached": True}

    name = target_name or target_id
    queries = [
        f"{name} inhibitor OR agonist pipeline clinical development 2026",
        f"{name} licensing OR acquisition OR partnership drug program",
        f"{name} phase 2 OR phase 3 trial initiated news",
    ]

    docs = await _gather_queries(queries, limit=2, use_cache=not refresh)
    summary = summarize.competitive_signal(name, docs)
    payload = {
        "target_id": target_id,
        "target_name": name,
        "content": summary["content"],
        "summarization_mode": summary["mode"],
        "has_signal": summary["ok"],
        "signal_count": len(docs),
        "sources": _sources(docs),
        "source_url": (_sources(docs)[0]["url"] if _sources(docs) else None),
        "items": [
            {"url": d["url"], "title": d.get("title", ""), "excerpt": d.get("text", "")[:500]}
            for d in docs
        ],
    }
    fetched_at = cache.put("competitive_signal", params, payload)
    return {**payload, "fetched_at": fetched_at, "cached": False}
