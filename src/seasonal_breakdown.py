"""
Season-by-season breakdown of the +EV book rules.

Answers: is the edge consistent across seasons, or does one lucky year
dominate the average?

Usage:
    python src/seasonal_breakdown.py
"""

import os
import glob
import re
from collections import defaultdict

import pandas as pd

from book_rules import BOOK_RULES
from evaluators import evaluate


HISTORICAL_DIR = os.path.join("data", "historical")
OUTPUT_DIR = "output"

REQUIRED_COLS = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'FTR',
                 'B365H', 'B365D', 'B365A']

# Rules to focus on — the +EV survivors from the corrected analysis
FOCUS_RULES = ["Book #11a", "Book #14", "Book #15a", "Book #3b", "Book #5b", "Book #2"]

# Realistic prices for combined markets (same as analyze_results.py)
PRICE_OVERRIDES = {
    "Book #1":  1.60,
    "Book #2":  1.90,
    "Book #6":  1.35,
    "Book #7":  1.20,
    "Book #9":  1.30,
    "Book #12": 1.35,
    "Book #16": 1.40,
    "Book #17": 1.25,
}


def season_from_filename(path: str) -> str:
    """E.g. E0_2324.csv -> 2324"""
    name = os.path.basename(path).replace(".csv", "")
    m = re.search(r"(\d{4})$", name)
    return m.group(1) if m else "unknown"


def ev(win_rate_pct: float, odds: float) -> float:
    p = win_rate_pct / 100
    return p * (odds - 1) - (1 - p)


def load_all_by_season():
    """Returns dict: season_code -> DataFrame"""
    files = sorted(glob.glob(os.path.join(HISTORICAL_DIR, "*.csv")))
    if not files:
        raise SystemExit(f"❌ No CSVs in {HISTORICAL_DIR}/.")

    by_season = defaultdict(list)
    for f in files:
        season = season_from_filename(f)
        try:
            df = pd.read_csv(f, encoding='utf-8', on_bad_lines='skip')
            missing = [c for c in REQUIRED_COLS if c not in df.columns]
            if missing:
                continue
            df = df[REQUIRED_COLS].copy()
            by_season[season].append(df)
        except Exception:
            continue

    out = {}
    for season, frames in by_season.items():
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.dropna(subset=['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A'])
        out[season] = combined
    return out


def compute_season_stats(df: pd.DataFrame, rule) -> dict:
    """Compute stats for one rule on one season's DataFrame."""
    n = 0
    wins = 0
    for _, row in df.iterrows():
        h = float(row['B365H'])
        d = float(row['B365D'])
        a = float(row['B365A'])
        om = {'H': h, 'D': d, 'A': a}
        band = om[rule.odds_field]
        if rule.odds_min <= band <= rule.odds_max:
            n += 1
            try:
                if evaluate(rule.play, row):
                    wins += 1
            except ValueError:
                pass

    if n == 0:
        return {'n': 0, 'wins': 0, 'hit_%': 0.0, 'roi_%': 0.0}

    hit = wins / n * 100
    price = PRICE_OVERRIDES.get(rule.id)
    if price is None:
        # Use the band's mid-point as the price (for straight-win and draw plays)
        price = (rule.odds_min + rule.odds_max) / 2
    roi = ev(hit, price) * 100

    return {'n': n, 'wins': wins, 'hit_%': round(hit, 1), 'roi_%': round(roi, 2)}


def main():
    print("📂 Loading data by season...")
    seasons = load_all_by_season()
    season_codes = sorted(seasons.keys())
    print(f"✅ {len(season_codes)} seasons: {', '.join(season_codes)}")

    # Build rule lookup
    rule_lookup = {r.id: r for r in BOOK_RULES}

    # Compute ROI matrix
    matrix = {}  # rule_id -> {season: stats}
    for rule_id in FOCUS_RULES:
        if rule_id not in rule_lookup:
            continue
        rule = rule_lookup[rule_id]
        matrix[rule_id] = {}
        for season in season_codes:
            matrix[rule_id][season] = compute_season_stats(seasons[season], rule)

    # Print season-by-season table for each rule
    print()
    print("=" * 118)
    print("📅 SEASON-BY-SEASON BREAKDOWN")
    print("=" * 118)

    for rule_id in FOCUS_RULES:
        if rule_id not in matrix:
            continue
        rule = rule_lookup[rule_id]

        print()
        print(f"── {rule_id}  |  {rule.play}  |  odds band {rule.odds_min}–{rule.odds_max} ──")
        print(f"{'Season':<10}{'N':<8}{'Wins':<8}{'Hit %':<10}{'ROI %':<10}")

        rois = []
        total_n = 0
        total_wins = 0
        for season in season_codes:
            s = matrix[rule_id][season]
            total_n += s['n']
            total_wins += s['wins']
            if s['n'] > 0:
                rois.append(s['roi_%'])
                print(f"{season:<10}{s['n']:<8}{s['wins']:<8}"
                      f"{s['hit_%']:<10}{s['roi_%']:<10.2f}")
            else:
                print(f"{season:<10}{'-':<8}{'-':<8}{'-':<10}{'-':<10}")

        if total_n > 0:
            overall_hit = total_wins / total_n * 100
            price = PRICE_OVERRIDES.get(rule_id, (rule.odds_min + rule.odds_max) / 2)
            overall_roi = ev(overall_hit, price) * 100

            if rois:
                mean_roi = sum(rois) / len(rois)
                variance = sum((r - mean_roi) ** 2 for r in rois) / len(rois)
                std_roi = variance ** 0.5
                positive_seasons = sum(1 for r in rois if r > 0)
                print(f"{'':<10}{'':<8}{'':<8}{'':<10}{'':<10}")
                print(f"{'OVERALL':<10}{total_n:<8}{total_wins:<8}"
                      f"{overall_hit:<10.1f}{overall_roi:<10.2f}")
                print(f"{'Mean ROI':<10}{mean_roi:<10.2f}")
                print(f"{'Std Dev':<10}{std_roi:<10.2f}   "
                      f"(lower = more consistent)")
                print(f"{'Positive':<10}{positive_seasons}/{len(rois)} seasons")

    print()
    print("=" * 118)
    print("How to read this:")
    print("  - If ROI is positive most seasons AND std dev is low → real edge")
    print("  - If one season carries the average → noise, not edge")
    print("  - If ROI flips positive/negative randomly → no signal")
    print("=" * 118)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "seasonal_breakdown.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Seasonal Breakdown\n\n")
        for rule_id in FOCUS_RULES:
            if rule_id not in matrix:
                continue
            rule = rule_lookup[rule_id]
            f.write(f"## {rule_id} — {rule.play}\n\n")
            f.write("| Season | N | Wins | Hit % | ROI % |\n")
            f.write("|--------|---|------|-------|-------|\n")
            rois = []
            for season in season_codes:
                s = matrix[rule_id][season]
                if s['n'] > 0:
                    rois.append(s['roi_%'])
                    f.write(f"| {season} | {s['n']} | {s['wins']} | {s['hit_%']} | {s['roi_%']} |\n")
                else:
                    f.write(f"| {season} | - | - | - | - |\n")
            if rois:
                mean = sum(rois) / len(rois)
                var = sum((r - mean) ** 2 for r in rois) / len(rois)
                std = var ** 0.5
                pos = sum(1 for r in rois if r > 0)
                f.write(f"\n**Mean ROI:** {mean:.2f}%  ")
                f.write(f"**Std Dev:** {std:.2f}  ")
                f.write(f"**Positive seasons:** {pos}/{len(rois)}\n\n")

    print(f"\n✅ Saved {out_path}")


if __name__ == "__main__":
    main()
