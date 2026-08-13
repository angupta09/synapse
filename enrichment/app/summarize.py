"""Summarization. Uses Claude when ANTHROPIC_API_KEY is set, extractive fallback otherwise.

Every summarizer here is grounded: it only ever sees retrieved source text and is
instructed to write from that text alone. Nothing is generated from model memory.
"""

import re
from typing import Optional

from .config import (
    ANTHROPIC_API_KEY,
    BEDROCK_MODEL_ID,
    BEDROCK_REGION,
    LLM_PROVIDER,
    LLM_MODEL,
)

_client = None


def _llm():
    """Lazily build whichever LLM client is configured (anthropic | bedrock | none)."""
    global _client
    if _client is not None:
        return _client
    if LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic

        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    elif LLM_PROVIDER == "bedrock":
        from anthropic import AnthropicBedrock

        _client = AnthropicBedrock(aws_region=BEDROCK_REGION)
    return _client


def _complete(system: str, user: str, max_tokens: int = 900) -> Optional[str]:
    client = _llm()
    if client is None:
        return None
    model = BEDROCK_MODEL_ID if LLM_PROVIDER == "bedrock" else LLM_MODEL
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()
    except Exception:
        return None


# Search-result and academic-index cruft that scrapes commonly drag in.
_CRUFT = [
    re.compile(r"^by\s+[A-Z]{1,3}\s+\w+.{0,40}?(Cited by \d+|·\s*\d{4})\s*[—–-]\s*", re.I),
    re.compile(r"\bCited by \d+\b", re.I),
    re.compile(r"\bRead more\b", re.I),
    re.compile(r"\b(Skip to|Jump to|Cookie|Privacy Policy|Terms of Use|Sign in|Subscribe)\b.*", re.I),
    re.compile(r"https?://\S+"),
]


def _scrub(sentence: str) -> str:
    for pattern in _CRUFT:
        sentence = pattern.sub("", sentence)
    return re.sub(r"\s{2,}", " ", sentence).strip(" -—–·|")


def _extractive(text: str, max_sentences: int = 4, safe_only: bool = False) -> str:
    """Fallback when no LLM key: take substantive source sentences verbatim.

    Verbatim source text cannot introduce a claim the source did not make. When
    `safe_only` is set (patient-facing path), sentences that would trip a
    patient-safety rule are skipped rather than emitted and then blocked — the
    gate still runs afterwards, this just avoids needlessly empty output.
    """
    from .rules import is_clean  # local import keeps this module import-cycle free

    clean = re.sub(r"\s+", " ", text).strip()
    picked: list[str] = []
    for raw in re.split(r"(?<=[.!?])\s+", clean):
        sentence = _scrub(raw)
        if len(sentence) < 40 or len(sentence) > 400:
            continue
        if safe_only and not is_clean(sentence):
            continue
        picked.append(sentence)
        if len(picked) >= max_sentences:
            break
    return " ".join(picked) if picked else ""


PATIENT_SYSTEM = """You write plain-language explanations of medical treatment options for patients and caregivers.

HARD RULES:
- Use ONLY facts stated in the provided source text. Never add information from your own knowledge.
- Never give dosing instructions, never tell the reader what they should take, and never state or imply a cure or guaranteed outcome.
- Never predict an individual's outcome. Describe what the treatment IS and what stage of study/approval it is at.
- Plain language, 8th-grade reading level, 3-5 sentences, calm and factual.
- End with: "Talk to your doctor about whether this is right for you."
- If the source text does not support a clear description, reply exactly: INSUFFICIENT_SOURCE"""

TRIAL_CONTEXT_SYSTEM = """You summarize public web context surrounding a specific clinical trial, for a pharma trial-design team.

HARD RULES:
- Use ONLY facts stated in the provided source text.
- Focus on: sponsor context, investigator/site details, stated rationale, reported progress or setbacks, and any stated reason a trial stopped or changed.
- Be specific and factual. No speculation, no filler.
- 3-6 sentences. If the source does not contain relevant trial context, reply exactly: INSUFFICIENT_SOURCE"""

COMPETITIVE_SYSTEM = """You summarize competitive-intelligence signal about a drug target or mechanism, for a pharma R&D/portfolio team.

HARD RULES:
- Use ONLY facts stated in the provided source text.
- Focus on: competitor programs, new trial starts, licensing/acquisition activity, conference presentations, notable investigator or academic activity, and development stage.
- Be specific: name companies, drugs, phases, and dates when the source states them.
- 3-6 sentences. If the source contains no competitive signal, reply exactly: INSUFFICIENT_SOURCE"""


def _summarize(
    system: str,
    context_label: str,
    docs: list[dict],
    max_tokens: int = 900,
    safe_only: bool = False,
) -> dict:
    """Shared summarization path. Returns {content, mode, ok}."""
    if not docs:
        return {"content": "", "mode": "none", "ok": False}

    joined = "\n\n---\n\n".join(
        f"SOURCE: {d.get('url','')}\nTITLE: {d.get('title','')}\n\n{d.get('text','')[:4000]}"
        for d in docs
    )
    user = f"{context_label}\n\nSOURCE TEXT:\n\n{joined}"

    out = _complete(system, user, max_tokens=max_tokens)
    if out and out.strip() != "INSUFFICIENT_SOURCE":
        return {"content": out.strip(), "mode": "llm", "ok": True}
    if out and out.strip() == "INSUFFICIENT_SOURCE":
        return {"content": "", "mode": "llm", "ok": False}

    joined_text = " ".join(d.get("text", "") for d in docs)
    content = _extractive(joined_text, safe_only=safe_only)
    return {"content": content, "mode": "extractive", "ok": bool(content)}


def patient_summary(treatment_name: str, condition_name: str, docs: list[dict]) -> dict:
    label = (
        f"Write a plain-language explanation of the treatment '{treatment_name}' "
        f"for someone living with '{condition_name}'."
    )
    return _summarize(PATIENT_SYSTEM, label, docs, max_tokens=600, safe_only=True)


def trial_context(nct_id: str, docs: list[dict]) -> dict:
    label = f"Summarize public context surrounding clinical trial {nct_id}."
    return _summarize(TRIAL_CONTEXT_SYSTEM, label, docs)


def competitive_signal(target_name: str, docs: list[dict]) -> dict:
    label = f"Summarize competitive intelligence signal around the target/mechanism '{target_name}'."
    return _summarize(COMPETITIVE_SYSTEM, label, docs)
