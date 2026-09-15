"""
Run all 17 book rules against every match in data/historical/

Usage:
    python src/run_backtest.py

Output:
    output/backtest_results.csv    — per-rule raw numbers
    output/backtest_summary.md     — human-readable report
"""

import os
import glob
import csv
from collections import defaultdict

import pandas as pd

from book_rules import BOOK_RULES
from evaluators import evaluate


HISTORICAL_DIR = os.path.join("data", "historical")
OUTPUT_DIR = "output"

REQUIRED_COLS = ['FTHG', 'FTAG', 'HTHG', 'HTAG', 'FTR',
                 'B365H', 'B365D', 'B365A']


def load_all() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(HISTORICAL_DIR, "*.csv")))
    if not files:
        raise SystemExit(
            f"❌ No CSVs in {HISTORICAL_DIR}/. Run fetch_data.py first."
        )

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding='utf-8', on_bad_lines='skip')
            missing = [c for c in REQUIRED_COLS if c not in df.columns]
            if missing:
                print(f"⚠️  {os.path.basename(f)}: missing {missing} — skipped")
                continue
            df = df[REQUIRED_COLS].copy()
            df['source'] = os.path.basename(f)
            frames.append(df)
        except Exception as e:
            print(f"⚠️  Skipped {f}: {e}")

    if not frames:
        raise SystemExit("❌ No usable CSVs found.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A'])
    return combined


def run(df: pd.DataFrame) -> list:
    stats = defaultdict(lambda: {'n': 0, 'wins': 0, 'odds_sum': 0.0})

    for _, row in df.iterrows():
        h = float(row['B365H'])
        d = float(row['B365D'])
        a = float(row['B365A'])
        om = {'H': h, 'D': d, 'A': a}

        for rule in BOOK_RULES:
            book_odds = om[rule.odds_field]
            if rule.odds_min <= book_odds <= rule.odds_max:
                s = stats[rule.id]
                s['n'] += 1
                s['odds_sum'] += book_odds
                try:
                    if evaluate(rule.play, row):
                        s['wins'] += 1
                except ValueError:
                    pass

    results = []
    for rule in BOOK_RULES:
        s = stats[rule.id]
        if s['n'] == 0:
            results.append({
                'id': rule.id, 'field': rule.odds_field,
                'play': rule.play, 'claimed_%': rule.claimed_confidence,
                'samples': 0, 'wins': 0, 'real_%': 0.0, 'gap': 0.0,
                'avg_odds': 0.0, 'verdict': 'no data',
            })
            continue

        real = s['wins'] / s['n'] * 100
        gap = real - rule.claimed_confidence
        avg_odds = s['odds_sum'] / s['n']

        if abs(gap) <= 5:
            verdict = '✅ aligned'
        elif gap > 5:
            verdict = f'🟢 UNDERSTATED (+{gap:.1f})'
        else:
            verdict = f'🔴 OVERSTATED ({gap:.1f})'

        results.append({
            'id': rule.id, 'field': rule.odds_field,
            'play': rule.play, 'claimed_%': rule.claimed_confidence,
            'samples': s['n'], 'wins': s['wins'],
            'real_%': round(real, 2), 'gap': round(gap, 2),
            'avg_odds': round(avg_odds, 3), 'verdict': verdict,
        })

    return results


def save_csv(results):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "backtest_results.csv")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"✅ Saved {path}")


def save_markdown(results):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "backtest_summary.md")

    with open(path, 'w', encoding='utf-8') as f:
        f.write("# Book vs Reality — Backtest Report\n\n")
        f.write("Testing the 17 odds-meaning rules from the Jay Soccer book (2018) ")
        f.write("against football-data.co.uk historical results.\n\n")
        f.write("| Rule | Field | Play | Claimed % | Samples | Real % | Gap | Verdict |\n")
        f.write("|------|-------|------|-----------|---------|--------|-----|---------|\n")
        for r in results:
            f.write(f"| {r['id']} | {r['field']} | {r['play']} | "
                    f"{r['claimed_%']} | {r['samples']} | {r['real_%']} | "
                    f"{r['gap']:+.1f} | {r['verdict']} |\n")

        f.write("\n## How to read\n\n")
        f.write("- ✅ aligned — book's confidence matches reality\n")
        f.write("- 🟢 UNDERSTATED — book is too pessimistic\n")
        f.write("- 🔴 OVERSTATED — book is overconfident\n")

    print(f"✅ Saved {path}")


def print_table(results):
    print()
    print("=" * 100)
    print("📖 BOOK vs REALITY")
    print("=" * 100)
    print(f"{'Rule':<12}{'Field':<6}{'Play':<28}{'Claim':<8}{'N':<8}{'Real':<8}{'Verdict'}")
    print("-" * 100)
    for r in results:
        if r['samples'] == 0:
            print(f"{r['id']:<12}{r['field']:<6}{r['play']:<28}"
                  f"{r['claimed_%']:<8}{0:<8}{'—':<8}no data")
        else:
            print(f"{r['id']:<12}{r['field']:<6}{r['play']:<28}"
                  f"{r['claimed_%']:<8}{r['samples']:<8}{r['real_%']:<8.1f}{r['verdict']}")
    print("=" * 100)


def main():
    print("📂 Loading historical data...")
    df = load_all()
    print(f"✅ Loaded {len(df):,} matches across {df['source'].nunique()} files")

    print("\n🔬 Testing 17 book rules...")
    results = run(df)

    print_table(results)
    save_csv(results)
    save_markdown(results)

    a = sum(1 for r in results if r['verdict'] == '✅ aligned')
    u = sum(1 for r in results if 'UNDERSTATED' in r['verdict'])
    o = sum(1 for r in results if 'OVERSTATED' in r['verdict'])
    nd = sum(1 for r in results if r['samples'] == 0)

    print(f"\n📊 Summary: ✅ {a} aligned  |  🟢 {u} understated  |  "
          f"🔴 {o} overstated  |  ⚠️  {nd} no data")


if __name__ == "__main__":
    main()
