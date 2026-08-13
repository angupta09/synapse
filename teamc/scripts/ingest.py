#!/usr/bin/env python3
"""Pull a real ClinicalTrials.gov cohort and build the Portal 2 risk model.

    python scripts/ingest.py --condition "amyotrophic lateral sclerosis"

Run this ONCE per disease area. It writes data/raw/*.jsonl and data/model.json.
The API only ever reads data/model.json — no request touches the network.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from teamc.ctgov import load_jsonl, pull_cohort  # noqa: E402
from teamc.failure_modes import MODE_LABELS, UNSPECIFIED, classify_why_stopped  # noqa: E402
from teamc.risk import RiskModel  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True,
                    help='disease area, e.g. "amyotrophic lateral sclerosis"')
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--out", default="data/model.json")
    ap.add_argument("--skip-fetch", action="store_true",
                    help="reuse whatever is already in --raw-dir")
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    if not args.skip_fetch:
        print(f"Pulling ClinicalTrials.gov v2 for: {args.condition}")
        pull_cohort(args.condition, raw)

    failed = load_jsonl(raw / "failed.jsonl")
    completed = load_jsonl(raw / "completed.jsonl")
    print(f"\nLoaded {len(failed)} terminated/withdrawn, {len(completed)} completed")

    # Classification report — always eyeball this before trusting the model.
    counts: dict[str, int] = {}
    for s in failed:
        why = ((s.get("protocolSection") or {}).get("statusModule") or {}).get("whyStopped")
        c = classify_why_stopped(why)
        counts[c.mode] = counts.get(c.mode, 0) + 1
    print("\nwhyStopped classification:")
    for mode, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        share = n / max(1, len(failed))
        print(f"  {MODE_LABELS.get(mode, mode):<48} {n:>4}  ({share:>5.1%})")
    unspec = counts.get(UNSPECIFIED, 0)
    if unspec / max(1, len(failed)) > 0.35:
        print(f"\n  ! {unspec / len(failed):.0%} unclassifiable. Consider running "
              f"scripts/adjudicate.py, or add lexicon rules — do NOT bucket these "
              f"into a mode to make the chart look better.")

    model = RiskModel.from_cohorts(
        condition=args.condition,
        failed_studies=failed,
        completed_studies=completed,
        source_note=f"ClinicalTrials.gov REST API v2, condition={args.condition!r}",
    )
    model.save(Path(args.out))
    print(f"\nModel written -> {args.out}")

    qualifying = sum(1 for c in model.cells.values() if c["qualifies"])
    print(f"Cohort modelled: {model._cohort_size} trials, "
          f"{model._n_failed} failures with a known reason")
    print(f"Qualifying (feature, value, mode) cells: {qualifying} of {len(model.cells)}")
    if qualifying == 0:
        print("\n  ! No feature cleared the support/lift/Wilson thresholds. Either the "
              "cohort is too small or this disease area has no design-linked failure "
              "signal. Try a broader condition term before loosening thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
