import json
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd
from pytrends.request import TrendReq

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# only the years the panel uses
FIRST_YEAR = 2016
# the final day itself is the result, not an expectation
WINDOW_DAYS = 30
OUT_DIR = os.path.join("raw", "trends")
OUT_CSV = "trends_results.csv"
# web keeps artist and song, a bare title like "hallucination" matches the
# plain word. on youtube a search is nearly always for music, so the title
# alone is safe there and gives about twice the coverage
PROPERTIES = {
    "web": ("", lambda artist, song: f"{artist} {song}"),
    "youtube": ("youtube", lambda artist, song: song),
}

# every country that votes, iso2 -> name as used in raw/{year}.json
TARGETS = {
    "AL": "Albania", "AM": "Armenia", "AT": "Austria", "AU": "Australia",
    "AZ": "Azerbaijan", "BE": "Belgium", "BG": "Bulgaria", "BY": "Belarus",
    "CH": "Switzerland", "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany",
    "DK": "Denmark", "EE": "Estonia", "ES": "Spain", "FI": "Finland",
    "FR": "France", "GB": "United Kingdom", "GE": "Georgia", "GR": "Greece",
    "HR": "Croatia", "HU": "Hungary", "IE": "Ireland", "IL": "Israel",
    "IS": "Iceland", "IT": "Italy", "LT": "Lithuania", "LU": "Luxembourg",
    "LV": "Latvia", "MD": "Moldova", "ME": "Montenegro", "MK": "North Macedonia",
    "MT": "Malta", "NL": "Netherlands", "NO": "Norway", "PL": "Poland",
    "PT": "Portugal", "RO": "Romania", "RS": "Serbia", "RU": "Russia",
    "SE": "Sweden", "SI": "Slovenia", "SM": "San Marino", "UA": "Ukraine",
}
NAME_TO_ISO = {name: iso for iso, name in TARGETS.items()}


def window(final_day):
    final = date.fromisoformat(final_day)
    start = final - timedelta(days=WINDOW_DAYS)
    end = final - timedelta(days=1)
    return f"{start.isoformat()} {end.isoformat()}"


def by_region(pytrends, term, timeframe, gprop, retries=6):
    """one term alone, so the values are a geographic profile and not a share"""
    for attempt in range(retries):
        try:
            pytrends.build_payload([term], timeframe=timeframe, gprop=gprop)
            frame = pytrends.interest_by_region(
                resolution="COUNTRY", inc_low_vol=True, inc_geo_code=True
            )
            return dict(zip(frame["geoCode"], frame[term].astype(int)))
        except Exception as exc:
            wait = 30 * 2**attempt
            print(f"  {exc.__class__.__name__}, waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"giving up on {term!r} after {retries} attempts")


def load(path):
    """an earlier result, so a rerun only asks for what changed"""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as file:
        result = json.load(file)
    # the first probe stored one shared term and bare values
    if "term" in result:
        term = result.pop("term")
        for name in PROPERTIES:
            result[name] = {"term": term, "values": result[name]}
    return result


def fetch_all(dataset_info):
    os.makedirs(OUT_DIR, exist_ok=True)
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 30))

    for year, info in sorted(dataset_info.items()):
        if int(year) < FIRST_YEAR:
            continue
        timeframe = window(info["date"])
        print(f"Processing {year} ({timeframe})")

        with open(info["path"], "r", encoding="utf-8") as file:
            entries = json.load(file)

        for country, entry in entries.items():
            artist, song = entry.get("artist"), entry.get("song")
            if not (artist and song):
                continue

            out_path = os.path.join(OUT_DIR, f"{country.replace(' ', '_')}_{year}.json")
            result = load(out_path) or {
                "year": int(year), "country": country, "artist": artist,
                "song": song, "timeframe": timeframe,
            }

            fetched = []
            for name, (gprop, make_term) in PROPERTIES.items():
                term = make_term(artist, song)
                if result.get(name, {}).get("term") == term:
                    continue
                values = by_region(pytrends, term, timeframe, gprop)
                result[name] = {"term": term, "values": values}
                fetched.append(name)
                time.sleep(8)

            if fetched:
                with open(out_path, "w", encoding="utf-8") as file:
                    json.dump(result, file, ensure_ascii=False, indent=1)
                print(f"  {country}: {', '.join(fetched)}")


def build_csv():
    rows = []
    for name in sorted(os.listdir(OUT_DIR)):
        with open(os.path.join(OUT_DIR, name), "r", encoding="utf-8") as file:
            result = json.load(file)
        home = NAME_TO_ISO.get(result["country"])
        if home is None:
            print(f"  no iso code for {result['country']}, home flag left false")
        for iso, target in TARGETS.items():
            rows.append({
                "year": result["year"],
                "song_country": result["country"],
                "song": result["song"],
                "artist": result["artist"],
                "target_country": target,
                "target_iso": iso,
                "trend_score": result["web"]["values"].get(iso, 0),
                "youtube_score": result["youtube"]["values"].get(iso, 0),
                "is_home_country": iso == home,
                "status": "success",
            })
    frame = pd.DataFrame(rows).sort_values(["year", "song_country", "target_iso"])
    frame.to_csv(OUT_CSV, index=False)
    zeros = (frame["trend_score"] == 0).mean()
    print(f"wrote {len(frame)} rows, {zeros:.1%} of web scores are zero")


if __name__ == "__main__":
    with open("dataset_info.json", "r", encoding="utf-8") as file:
        dataset_info = json.load(file)
    fetch_all(dataset_info)
    build_csv()
