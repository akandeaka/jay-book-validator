"""
Turn hit-rate results into actual profit/loss per rule.

A rule can hit 80% and still lose money if the odds are too short.
This script computes:
    - Expected value per unit staked
    - ROI% per rule
    - Kelly fraction (optimal stake)

Usage:
    python src/analyze_results.py
"""

import csv
import os


RESULTS_CSV = os.path.join("output", "backtest_results.csv")
OUTPUT_MD = os.path.join("output", "profit_analysis.md")


def expected_value(win_rate_pct: float, avg_odds: float) -> float:
    """EV per 1 unit staked."""
    p = win_rate_pct / 100
    return p * (avg_odds - 1) - (1 - p)


def kelly_fraction(win_rate_pct: float, avg_odds: float) -> float:
    """Optimal fraction of bankroll. Negative = don't bet."""
    p = win_rate_pct / 100
    b = avg_odds - 1
    if b <= 0:
        return 0.0
    return (p * b - (1 - p)) / b


def main():
    if not os.path.exists(RESULTS_CSV):
        raise SystemExit(f"❌ {RESULTS_CSV} not found. Run run_backtest.py first.")

    with open(RESULTS_CSV, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    print()
    print("=" * 100)
    print("💰 PROFITABILITY ANALYSIS")
    print("=" * 100)
    print(f"{'Rule':<12}{'Play':<30}{'N':<8}{'Real %':<9}{'Avg odds':<11}"
          f"{'EV':<10}{'ROI %':<10}{'Kelly':<10}{'Flag'}")
    print("-" * 100)

    enriched = []
    for r in rows:
        n = int(r['samples'])
        if n == 0:
            continue
        real = float(r['real_%'])
        odds = float(r['avg_odds'])
        if odds <= 1.0:
            continue

        e = expected_value(real, odds)
        roi = e * 100
        k = kelly_fraction(real, odds)

        r['EV'] = round(e, 4)
        r['ROI_%'] = round(roi, 2)
        r['Kelly'] = round(k, 4)
        r['profitable'] = e > 0
        enriched.append(r)

        flag = "🟢 +EV" if e > 0 else "🔴 -EV"
        print(f"{r['id']:<12}{r['play']:<30}{n:<8}{real:<9.1f}{odds:<11.3f}"
              f"{e:<10.4f}{roi:<10.2f}{k:<10.4f}{flag}")

    print("=" * 100)

    profitable = [r for r in enriched if r['profitable']]
    print(f"\n📊 {len(profitable)} / {len(enriched)} rules show positive expected value.")

    if profitable:
        print("\n🟢 Positive-EV rules (best first):")
        for r in sorted(profitable, key=lambda x: -float(x['ROI_%'])):
            print(f"   {r['id']:<12} {r['play']:<30} ROI: {r['ROI_%']:+.2f}%")

    losers = [r for r in enriched if not r['profitable']]
    if losers:
        print("\n🔴 Negative-EV rules:")
        for r in sorted(losers, key=lambda x: float(x['ROI_%'])):
            print(f"   {r['id']:<12} {r['play']:<30} ROI: {r['ROI_%']:+.2f}%")

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("# Profitability Analysis\n\n")
        f.write("Hit rate alone doesn't matter — this table shows **expected value per unit staked**.\n\n")
        f.write("| Rule | Play | Samples | Real % | Avg Odds | EV | ROI % | Kelly | Verdict |\n")
        f.write("|------|------|---------|--------|----------|-----|-------|-------|---------|\n")
        for r in enriched:
            v = "🟢 +EV" if r['profitable'] else "🔴 -EV"
            f.write(f"| {r['id']} | {r['play']} | {r['samples']} | {r['real_%']} | "
                    f"{r['avg_odds']} | {r['EV']} | {r['ROI_%']} | {r['Kelly']} | {v} |\n")

    print(f"\n✅ Saved {OUTPUT_MD}")


if __name__ == "__main__":
    main()
