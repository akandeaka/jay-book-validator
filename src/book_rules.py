"""
The 17 odds-meaning rules from "How to Make Over a Million at the Start of
Every New Football Season" (Justin Onyeka / Jay Soccer Predictions, 2018).

Each rule is a dataclass for easy iteration, filtering, and reporting.
"""

from dataclasses import dataclass


@dataclass
class BookRule:
    id: str
    odds_field: str
    odds_min: float
    odds_max: float
    play: str
    claimed_confidence: int
    claimed_odds: float
    season_note: str = "any"
    source_page: int = 0


BOOK_RULES = [
    # --- 1.1x to 1.2x home favourites ---
    BookRule("Book #1",   'H', 1.13, 1.15, "Under 1.5 HT",                  70, 1.14, source_page=13),
    BookRule("Book #2",   'H', 1.18, 1.20, "Home + Over 2.5 FT",            70, 1.19, season_note="early", source_page=13),
    BookRule("Book #3a",  'H', 1.21, 1.23, "Straight Home Win",             90, 1.22, source_page=13),
    BookRule("Book #3b",  'H', 1.25, 1.27, "Straight Home Win",             90, 1.26, source_page=13),
    BookRule("Book #3c",  'H', 1.27, 1.29, "Straight Home Win",             90, 1.28, source_page=13),
    BookRule("Book #4",   'H', 1.24, 1.26, "Avoid (trap)",                  50, 1.25, source_page=14),
    BookRule("Book #5a",  'H', 1.29, 1.31, "Straight Home Win",             85, 1.30, season_note="early", source_page=14),
    BookRule("Book #5b",  'H', 1.35, 1.37, "Straight Home Win",             85, 1.36, season_note="early", source_page=14),
    BookRule("Book #6",   'H', 1.29, 1.31, "1X & Under 3.5",                80, 1.30, season_note="early", source_page=14),
    BookRule("Book #7",   'H', 1.39, 1.45, "1X & Under 4.5",                78, 1.42, source_page=14),
    BookRule("Book #8a",  'H', 1.49, 1.51, "Straight Home Win",             82, 1.50, source_page=15),
    BookRule("Book #8b",  'H', 1.56, 1.58, "Straight Home Win",             82, 1.57, source_page=15),
    BookRule("Book #9",   'A', 1.52, 1.54, "X2 & Under 3.5",                75, 1.53, source_page=15),
    BookRule("Book #10",  'H', 1.56, 1.58, "Straight Home Win",             75, 1.57, source_page=15),
    BookRule("Book #11a", 'H', 1.71, 1.73, "Straight Home Win",             80, 1.72, source_page=15),
    BookRule("Book #11b", 'H', 1.79, 1.81, "Straight Home Win",             80, 1.80, source_page=15),
    BookRule("Book #12",  'H', 1.89, 1.91, "1X & Under 3.5",                72, 1.90, source_page=15),
    BookRule("Book #13a", 'H', 1.99, 2.01, "Straight Home Win",             65, 2.00, source_page=15),
    BookRule("Book #13b", 'H', 2.09, 2.11, "Straight Home Win",             65, 2.10, source_page=15),

    # --- Draw odds bands ---
    BookRule("Book #14",  'D', 2.99, 3.01, "FT Draw",                       30, 3.00, source_page=16),
    BookRule("Book #15a", 'D', 3.24, 3.26, "FT Draw",                       30, 3.25, source_page=16),
    BookRule("Book #15b", 'D', 3.28, 3.30, "FT Draw",                       30, 3.29, source_page=16),
    BookRule("Book #16",  'D', 3.38, 3.40, "BTTS or Over 2.5",              60, 3.39, source_page=16),
    BookRule("Book #17",  'D', 3.58, 3.62, "Over 0.5 HT or Over 3.5 FT",    65, 3.60, season_note="early", source_page=16),
]
