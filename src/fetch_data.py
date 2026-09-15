"""
Download historical CSVs from football-data.co.uk into data/historical/

Free, no API key. This script only downloads — no analysis.

Usage:
    python src/fetch_data.py
"""

import os
import urllib.request


OUTPUT_DIR = os.path.join("data", "historical")
BASE_URL = "https://www.football-data.co.uk/mmz4281"

# Season codes used by football-data.co.uk: "2324" = 2023/24 season
SEASONS = ["1415", "1516", "1617", "1718", "1819", "1920",
           "2021", "2122", "2223", "2324", "2425"]

# League codes:
#   E0/E1  — England Premier League / Championship
#   D1/D2  — Germany Bundesliga / 2. Bundesliga
#   SP1/SP2 — Spain La Liga / Segunda
#   I1/I2  — Italy Serie A / Serie B
#   F1/F2  — France Ligue 1 / Ligue 2
#   N1     — Netherlands Eredivisie
#   P1     — Portugal Primeira Liga
#   T1     — Turkey Süper Lig
#   B1     — Belgium Pro League
LEAGUES = ["E0", "E1", "D1", "D2", "SP1", "SP2", "I1", "I2",
           "F1", "F2", "N1", "P1", "T1", "B1"]


def download(season: str, league: str) -> bool:
    """Download one CSV. Returns True if downloaded or already exists."""
    filename = f"{league}_{season}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath):
        print(f"   ✓ {filename} (already exists)")
        return True

    url = f"{BASE_URL}/{season}/{league}.csv"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"   ✅ {filename} ({len(data):,} bytes)")
        return True
    except Exception as e:
        print(f"   ❌ {filename}: {e}")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("📥 Downloading historical data from football-data.co.uk")
    print("=" * 70)
    print(f"Seasons: {', '.join(SEASONS)}")
    print(f"Leagues: {', '.join(LEAGUES)}")
    print(f"Target:  {OUTPUT_DIR}/")
    print()

    success, failed = 0, 0

    for season in SEASONS:
        print(f"📅 Season {season}:")
        for league in LEAGUES:
            if download(season, league):
                success += 1
            else:
                failed += 1
        print()

    print("=" * 70)
    print(f"✅ Downloaded: {success}   ❌ Failed: {failed}")
    print(f"📁 Files in {OUTPUT_DIR}/: {len(os.listdir(OUTPUT_DIR))}")
    print("=" * 70)


if __name__ == "__main__":
    main()
