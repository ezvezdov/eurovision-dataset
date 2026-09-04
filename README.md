# Eurovision Song Contest Dataset

A collection of Eurovision Song Contest Grand Final results, scraped/compiled per year into individual JSON files.

## Coverage

- **Years:** 2008–2025
- **Excluded:** 2010 (no official Grand Final video playlist could be found — see [sources.md](sources.md))
- **Scope:** Grand Final only (no Semi-Finals)
- **Sources:** Wikipedia result pages and official Eurovision YouTube playlists, listed per year in [sources.md](sources.md)

## Repository structure

```
eurovision-dataset/
├── 2008.json
├── 2009.json
├── 2011.json
├── ...
├── 2025.json
├── sources.md   # source links (Wikipedia + YouTube) used per year
└── LICENSE
```

Each `<year>.json` file contains the Grand Final results for that year's contest.

## File format

Each JSON file is an object keyed by **country name**, where the value is an object describing that country's entry:

```json
{
  "Austria": {
    "artist": "JJ",
    "song": "Wasted Love",
    "points": 436,
    "title": "JJ – Wasted Love (LIVE) | Austria 🇦🇹 | Grand Final | Winner of Eurovision 2025",
    "link": "https://www.youtube.com/watch?v=onOex2WXjbA",
    "year": "2025"
  },
  "Israel": {
    "artist": "Yuval Raphael",
    "song": "New Day Will Rise",
    "points": 357,
    "title": "Yuval Raphael – New Day Will Rise (LIVE) | Israel 🇮🇱 | Grand Final | Eurovision 2025",
    "link": "https://www.youtube.com/watch?v=_7zHp51j2WM",
    "year": "2025"
  }
}
```

### Fields

| Field    | Type   | Description                                                                                     |
|----------|--------|---------------------------------------------------------------------------------------------------|
| *(key)*  | string | The competing country's name. Used as the top-level object key, not a field inside the entry.     |
| `artist` | string | Name of the performing artist(s)/act representing the country.                                    |
| `song`   | string | Title of the competing song.                                                                       |
| `points` | int    | Total points awarded to the entry in the Grand Final (juries + televote combined).                 |
| `title`  | string | Title of the official YouTube video of the live performance (as published on the Eurovision channel). |
| `link`   | string | URL to the official YouTube video of the live performance.                                         |
| `year`   | string | Contest year, matching the file name (e.g. `"2025"`).                                              |

### Notes

- Countries are **not pre-sorted** by rank/points in the JSON object; sort by `points` (descending) if you need the final leaderboard.
- The number of countries varies by year (25–27), reflecting the different number of Grand Final qualifiers each year.
- `points` reflects the combined jury + televote scoring system in place for that year; scoring rules changed slightly over the contest's history (e.g., introduction of separate jury/televote scores in 2016), but only the final combined score is recorded here.

## Example usage (Python)

```python
import json

with open("2025.json", encoding="utf-8") as f:
    data = json.load(f)

# Winner of the 2025 Grand Final
winner = max(data.items(), key=lambda kv: kv[1]["points"])
country, entry = winner
print(f"{country}: {entry['artist']} — {entry['song']} ({entry['points']} points)")
```

## License

Released under the [GNU General Public License v3.0](LICENSE).
