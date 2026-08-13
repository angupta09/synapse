"""Pre-fetch and PIN every enrichment call the live demo touches.

Run this well before demo time. Pinned cache entries never expire, so nothing
in the demo path depends on a live Bright Data call completing on stage.

    python -m scripts.prefetch
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import cache, enrichment  # noqa: E402
from app.config import HAS_BRIGHTDATA, HAS_LLM  # noqa: E402

TARGETS = Path(__file__).resolve().parent.parent / "demo_targets.json"


async def main() -> int:
    cache.init()
    cfg = json.loads(TARGETS.read_text())

    print(f"Disease area : {cfg['disease_area']}")
    print(f"Bright Data  : {'configured' if HAS_BRIGHTDATA else 'MISSING TOKEN'}")
    print(f"Summarizer   : {'claude' if HAS_LLM else 'extractive fallback'}")
    print("-" * 60)

    if not HAS_BRIGHTDATA:
        print("ERROR: BRIGHTDATA_API_TOKEN not set. Copy .env.example -> .env first.")
        return 1

    ok, failed = 0, 0

    for item in cfg["patient_summaries"]:
        label = f"patient-summary {item['treatment_name']} / {item['condition_name']}"
        try:
            res = await enrichment.patient_summary(
                item["condition_id"],
                item["treatment_id"],
                item["condition_name"],
                item["treatment_name"],
                refresh=True,
            )
            cache.pin(
                "patient_summary",
                {"condition_id": item["condition_id"], "treatment_id": item["treatment_id"]},
            )
            gate = "PASS" if res["safety"]["passed"] else "BLOCKED"
            print(f"  [{gate:7}] {label}  ({len(res['sources'])} sources)")
            if not res["safety"]["passed"]:
                for v in res["safety"]["violations"]:
                    print(f"            reason: {v['reason']}")
            ok += 1
        except Exception as exc:
            print(f"  [ERROR  ] {label}: {exc}")
            failed += 1

    for item in cfg["trial_contexts"]:
        label = f"trial-context {item['nct_id']}"
        try:
            res = await enrichment.trial_context(
                item["nct_id"], item.get("trial_title", ""), refresh=True
            )
            cache.pin("trial_context", {"nct_id": item["nct_id"]})
            print(f"  [OK     ] {label}  ({len(res['sources'])} sources)")
            ok += 1
        except Exception as exc:
            print(f"  [ERROR  ] {label}: {exc}")
            failed += 1

    for item in cfg["competitive_signals"]:
        label = f"competitive-signal {item['target_name']}"
        try:
            res = await enrichment.competitive_signal(
                item["target_id"], item.get("target_name", ""), refresh=True
            )
            cache.pin("competitive_signal", {"target_id": item["target_id"]})
            print(f"  [OK     ] {label}  ({len(res['sources'])} sources)")
            ok += 1
        except Exception as exc:
            print(f"  [ERROR  ] {label}: {exc}")
            failed += 1

    print("-" * 60)
    print(f"Prefetched {ok} entries, {failed} failed. All successful entries are PINNED.")
    print(json.dumps(cache.stats(), indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
