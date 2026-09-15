"""Evaluate whether a book play won, given the real score."""

import pandas as pd


def evaluate(play: str, row: pd.Series) -> bool:
    """
    Given a play description and a row from football-data.co.uk, return True if it won.

    Columns used:
        FTHG, FTAG  — full-time home/away goals
        HTHG, HTAG  — half-time home/away goals
        FTR         — 'H', 'D', 'A'
    """
    hg = int(row['FTHG'])
    ag = int(row['FTAG'])
    ht_hg = int(row['HTHG']) if not pd.isna(row['HTHG']) else 0
    ht_ag = int(row['HTAG']) if not pd.isna(row['HTAG']) else 0
    total = hg + ag
    ht_total = ht_hg + ht_ag
    p = play.lower()

    # ---------- straight results ----------
    if p == "straight home win":
        return hg > ag

    if p == "home + over 2.5 ft":
        return hg > ag and total > 2

    # ---------- double-chance combos ----------
    if "1x & under 3.5" in p:
        return hg >= ag and total < 4
    if "1x & under 4.5" in p:
        return hg >= ag and total < 5
    if "x2 & under 3.5" in p:
        return ag >= hg and total < 4

    # ---------- draws ----------
    if p == "ft draw":
        return hg == ag

    # ---------- goals ----------
    if p == "under 1.5 ht":
        return ht_total < 2
    if p == "over 0.5 ht":
        return ht_total > 0
    if p == "over 2.5":
        return total > 2
    if p == "over 3.5":
        return total > 3
    if p == "btts or over 2.5":
        return (hg > 0 and ag > 0) or total > 2
    if p == "over 0.5 ht or over 3.5 ft":
        return ht_total > 0 or total > 3

    # ---------- trap rule ----------
    if p.startswith("avoid"):
        # The "trap" claim = the favourite fails to win
        return hg <= ag

    raise ValueError(f"Unknown play: {play}")
