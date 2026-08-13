"""Verify the service works end to end. Run before wiring anyone else in.

    python -m scripts.smoke_test
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import brightdata, cache, safety  # noqa: E402
from app.config import HAS_BRIGHTDATA, HAS_LLM  # noqa: E402


def check(label: str, passed: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if passed else 'FAIL'}] {label}{'  — ' + detail if detail else ''}")
    return passed


async def main() -> int:
    cache.init()
    results = []

    print("\n1. Config")
    results.append(check("Bright Data token set", HAS_BRIGHTDATA))
    print(f"       LLM summarizer: {'claude' if HAS_LLM else 'extractive fallback (fine)'}")

    print("\n2. Safety gate (offline — must work regardless of network)")
    bad_cases = [
        ("Take 50 mg daily with food.", "dosing"),
        ("This drug cures ALS in most patients.", "cure_claim"),
        ("It is completely safe with no side effects.", "guarantee"),
        ("You should stop taking your current medication.", "directive"),
    ]
    for text, expected_rule in bad_cases:
        violations = safety.check_patterns(text)
        hit = any(v["rule"] == expected_rule for v in violations)
        results.append(check(f"blocks {expected_rule!r}", hit, text[:40]))

    good = (
        "Riluzole is an approved medicine for ALS. It is thought to reduce damage to "
        "motor neurons by lowering glutamate levels in the brain and spinal cord. In "
        "studies it modestly extended survival for some people. Talk to your doctor "
        "about whether this is right for you."
    )
    results.append(check("allows clean patient text", not safety.check_patterns(good)))

    gated = safety.gate(good, [{"url": "https://www.nih.gov/example", "text": good}])
    results.append(check("gate passes clean+sourced content", gated["passed"]))

    ungated = safety.gate(good, [{"url": "", "text": good}])
    results.append(check("gate blocks unsourced content", not ungated["passed"]))

    print("\n3. Bright Data connectivity")
    if not HAS_BRIGHTDATA:
        print("  [SKIP] no token configured")
    else:
        try:
            hits = await brightdata.search("amyotrophic lateral sclerosis treatment", num=5)
            results.append(check("SERP search returns results", len(hits) > 0, f"{len(hits)} hits"))
            if hits:
                doc = await brightdata.scrape(hits[0]["url"])
                results.append(
                    check("Web Unlocker scrape returns text", bool(doc), hits[0]["url"][:50])
                )
        except Exception as exc:
            results.append(check("Bright Data reachable", False, str(exc)[:120]))

    print("\n3b. Content hygiene (offline)")
    results.append(
        check("rejects google redirect urls", not brightdata._is_usable_url("/goto?url=CAESYQ"))
    )
    results.append(
        check("rejects pdf urls", not brightdata._is_usable_url("https://example.org/paper.pdf"))
    )
    results.append(
        check("accepts normal urls", brightdata._is_usable_url("https://www.nih.gov/als"))
    )
    results.append(
        check("detects binary content", brightdata._looks_binary("T�d� �9g�*r��e��b�v*�l"))
    )
    results.append(
        check("accepts readable prose", not brightdata._looks_binary("Riluzole is approved for ALS."))
    )

    print("\n4. Cache")
    cache.put("smoke", {"k": "v"}, {"hello": "world"})
    results.append(check("cache write/read round-trip", cache.get("smoke", {"k": "v"}) is not None))

    passed = sum(results)
    print(f"\n{passed}/{len(results)} checks passed\n")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
