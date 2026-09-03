# Data Sources — taskmaster

All data used in this project is from authoritative sources. Crowd-edited
references (Wikipedia, etc.) are not used as primary *data* sources — but are
acceptable, and here used, as a **name/spelling reference** cross-checked
against the show's own broadcast credits.

---

## Sources

### Contestant total points by series (hand-collected)
- **Publisher:** Author (hand-collected from the Taskmaster UK scoreboards shown on-air / on the official Taskmaster scoreboard).
- **URL:** local (hand-collected; not fetched from a network source)
- **Format:** CSV, hand-curated
- **License:** Facts (scores) are not copyrightable; compiled dataset released by the author.
- **Fields used:** `Series Number`, `Contestant Name`, `Total Points`
- **Coverage:** Taskmaster UK main series 1–21 (2015–2026). Five contestants per series, 105 rows. Excludes Champion of Champions and New Year Treat specials, and excludes Junior Taskmaster.
- **How the source collects the data:** Each episode, Greg Davies awards points per task; the cumulative total across all episodes in a series is the contestant's series total. Values here were transcribed by hand from the per-series scoreboards.
- **How the source defines the data:** "Total Points" = sum of all points a contestant earned across every task in their series (prize tasks + filmed tasks + studio/live tasks), as adjudicated on the show. It is the raw series total, NOT normalized for the number of episodes/tasks in that series.
- **Methodology changes / series breaks:** **This is the key caveat of the dataset.** The number of episodes — and therefore the number of tasks and total points available — is NOT constant across series. Series 1 had 6 episodes; series 2–3 had 5; series 4–5 had 8; series 6 onward had 10. As a result, raw totals are NOT comparable across series (a contestant in a 10-episode series can amass far more points than a winner of a 5-episode series). Comparisons across series MUST use the normalized **share of series points** (each contestant's points ÷ that series' total), computed during data preparation.
- **Known controversies / debates:** Points are awarded subjectively by the Taskmaster for comedic effect; disputed/adjusted scores, bonus points, and penalties happen. Totals reflect the show's final on-air adjudication, not an objective performance metric.
- **Notes:** Original hand-collected data used first names only and contained spelling errors; names were corrected to official full names (see cast reference below) before ingest.
- **Retrieved:** 2026-09-01

### Per-series cast — full names (name reference only)
- **Publisher:** Wikipedia, "List of Taskmaster episodes" (each series' five contestants are named in prose, sourced there to the British Comedy Guide episode guides and the broadcaster).
- **URL:** https://en.wikipedia.org/wiki/List_of_Taskmaster_episodes
- **Format:** HTML (read as reference, not ingested as data)
- **License:** CC BY-SA (text). Used here only to verify name spellings; the underlying facts (who competed) are also in the on-air credits.
- **Fields used:** Contestant full names per series 1–21.
- **Coverage:** UK main series 1–21.
- **How the source collects the data:** Editorially compiled from broadcast credits and press announcements, cited to the British Comedy Guide episode guides and Channel 4 / Dave.
- **How the source defines the data:** The five headline contestants credited for each numbered series.
- **Methodology changes / series breaks:** N/A (name reference).
- **Known controversies / debates:** None relevant to name spelling. (Series 9 had stand-ins for studio segments and series 20 required a tie-breaker, but the five credited contestants are unambiguous.)
- **Notes:** Used solely to map hand-collected first names to accurate full names and fix misspellings (e.g. "Fahtia" → Fatiha El-Ghorri, "Kaell" → Kiell Smith-Bynoe, "Lollie" → Lolly Adefope, "Maesie" → Maisie Adam, "Carrie" → Kerry Godliman).
- **Retrieved:** 2026-09-01

---

## Notes on Data Quality

- The hand-collected source values are preserved verbatim; corrections to the raw values are made deliberately and documented here.
- **Point values validated (2026-09-01)** against the Taskmaster Fandom "Contestant Statistics" per-episode scoreboards (S1-20) and the Digital Spy series-21 leaderboard, cross-checked on individual contestant pages. The values were hand-transcribed from on-screen finales (iPad + Apple Pencil, OCR to CSV), so were checked for digit misreads. Two errors were found and corrected:
  - **S10 Katherine Parkinson: 148 → 118.** Handwriting/OCR digit misread (4↔1). Confirmed last place at 118 by two sources. The wrong value had placed her mid-table instead of last.
  All 104 other values matched the reference exactly.
- **S20 Maisie Adam recorded as 152 (scoreboard 151) — deliberate, not an error.** Series 20 ended in a three-way tie on 151 points (Adam, Magliano, Ellis); Maisie Adam won a live tie-breaker task to become the series champion. Rather than leave a three-way rank-1 tie that misrepresents the outcome, we add the tie-break as +1 so Adam is recorded at 152 and stands as the sole S20 winner. This is an editorial adjudication adjustment, documented here for transparency; the raw scoreboard total was 151.
- **The primary series break is episode count.** Raw `total_points` is not comparable across series. Always compare on `pct_of_series_points` (share of the series' total) or within-series `series_rank`. This is stated in the codebook and every chart footnote.
- Points are a subjective, comedic score — treat cross-contestant comparison as entertainment, not a skill ranking.
