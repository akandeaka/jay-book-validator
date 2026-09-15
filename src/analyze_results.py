"""
Turn hit-rate results into actual profit/loss per rule.

Fix: for rules where the play is NOT "Straight Home Win" or "FT Draw",
the odds band that triggered the rule is NOT the price of the actual bet.
We use a realistic price estimate for those markets instead.

Usage:
    python src/analyze_results.py
"""

import csv
import os


RESULTS_CSV = os.path.join("output", "backtest_results.csv")
OUTPUT_MD = os.path.join("output", "profit_analysis.md")


# ============================================================
# REALISTIC PRICE ESTIMATES FOR COMBINED / DERIVED MARKETS
# ------------------------------------------------------------
# These are approximate market prices for the actual bet being placed,
# not the odds band that triggered the rule.
#
# If the play matches the odds band directly (Straight Home Win, FT Draw),
# we use the actual odds from the data. Otherwise, we substitute.
# ============================================================

PRICE_OVERRIDES = {
    # Rule id: (realistic_price, reason)
    "Book #1":  (1.60, "Under 1.5 HT — half-time under markets trade ~1.55–1.65"),
    "Book #2":  (1.90, "Home + Over 2.5 FT — combined ~1.85–1.95"),
    "Book #6":  (1.35, "1X & Under 3.5 — combined ~1.30–1.40"),
    "Book #7":  (1.20, "1X & Under 4.5 — combined ~1.15–1.25"),
    "Book #9":  (1.30, "X2 & Under 3.5 — combined ~1.25–1.35"),
    "Book #12": (1.35, "1X & Under 3.5 — combined ~1.30–1.40"),
    "Book #16": (1.40, "BTTS or Over 2.5 — combined ~1.35–1.45"),
    "Book #17": (1.25, "Over 0.5 HT or Over 3.5 FT — heavy favourite combo ~1.20–1.30"),
}


def ev(win_rate_pct: float, avg_odds: float) -> float:
    """Expected value per 1 unit staked."""
    p = win_rate_pct / 100
    return p * (avg_odds - 1) - (1 - p)


def kelly(win_rate_pct: float, avg_odds: float) -> float:
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
    print("=" * 118)
    print("💰 PROFITABILITY ANALYSIS (corrected pricing)")
    print("=" * 118)
    print(f"{'Rule':<12}{'Play':<30}{'N':<8}{'Real %':<9}{'Band':<9}"
          f"{'Price':<9}{'Source':<12}{'EV':<10}{'ROI %':<10}{'Flag'}")
    print("-" * 118)

    enriched = []
    for r in rows:
        n = int(r['samples'])
        if n == 0:
            continue
        real = float(r['real_%'])
        band_odds = float(r['avg_odds'])
        if band_odds <= 1.0:
            continue

        # Decide which price to use for this rule
        rule_id = r['id']
        if rule_id in PRICE_OVERRIDES:
            price, reason = PRICE_OVERRIDES[rule_id]
            source = "est."
        else:
            price = band_odds
            source = "actual"

        e = ev(real, price)
        roi = e * 100
        k = kelly(real, price)

        r['EV'] = round(e, 4)
        r['ROI_%'] = round(roi, 2)
        r['Kelly'] = round(k, 4)
        r['price_used'] = round(price, 3)
        r['price_source'] = source
        r['profitable'] = e > 0
        enriched.append(r)

        flag = "🟢 +EV" if e > 0 else "🔴 -EV"
        print(f"{r['id']:<12}{r['play']:<30}{n:<8}{real:<9.1f}{band_odds:<9.3f}"
              f"{price:<9.3f}{source:<12}{e:<10.4f}{roi:<10.2f}{flag}")

    print("=" * 118)
    print("Band = odds band that triggered the rule  |  "
          "Price = price used in EV calculation  |  "
          "Source = actual (from data) or est. (substituted)")

    profitable = [r for r in enriched if r['profitable']]
    print(f"\n📊 {len(profitable)} / {len(enriched)} rules show positive expected value.")

    if profitable:
        print("\n🟢 Positive-EV rules (best first):")
        for r in sorted(profitable, key=lambda x: -float(x['ROI_%'])):
            print(f"   {r['id']:<12} {r['play']:<30} "
                  f"ROI: {r['ROI_%']:+7.2f}%   (price: {r['price_used']}, {r['price_source']})")

    losers = [r for r in enriched if not r['profitable']]
    if losers:
        print("\n🔴 Negative-EV rules (worst first):")
        for r in sorted(losers, key=lambda x: float(x['ROI_%'])):
            print(f"   {r['id']:<12} {r['play']:<30} "
                  f"ROI: {r['ROI_%']:+7.2f}%")

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("# Profitability Analysis (corrected pricing)\n\n")
        f.write("Hit rate alone doesn't matter — this table shows **expected value per unit staked**.\n\n")
        f.write("**Important:** For rules where the actual bet is NOT the odds band "
                "(e.g. combined markets like BTTS or Over 2.5), the EV uses a realistic "
                "market price, not the draw odds. `Source` column shows whether the price "
                "came from the data (`actual`) or was substituted (`est.`).\n\n")
        f.write("| Rule | Play | Samples | Real % | Band Odds | Price Used | Source | "
                "EV | ROI % | Kelly | Verdict |\n")
        f.write("|------|------|---------|--------|-----------|------------|--------|"
                "-----|-------|-------|---------|\n")
        for r in enriched:
            v = "🟢 +EV" if r['profitable'] else "🔴 -EV"
            f.write(f"| {r['id']} | {r['play']} | {r['samples']} | {r['real_%']} | "
                    f"{r['avg_odds']} | {r['price_used']} | {r['price_source']} | "
                    f"{r['EV']} | {r['ROI_%']} | {r['Kelly']} | {v} |\n")

    print(f"\n✅ Saved {OUTPUT_MD}")


if __name__ == "__main__":
    main()
