# Mini-Grid Site Prioritization Tool

A small, real-data tool that answers one concrete question for a solar
mini-grid / off-grid energy company operating in Kenya:

> **"Given limited capital, which county — or which specific
> constituency — should we invest in next?"**

Instead of guessing or relying on anecdote, this ranks all 47 Kenyan
counties by an **opportunity score** built from real government data,
now including a solar resource factor, plus a finer-grained real
constituency-level ranking, and a Streamlit app so a non-technical
analyst can move the weight sliders themselves.

## Why this exists

Off-grid solar and mini-grid companies decide where to build using a mix
of intuition, sales-team anecdotes, and slow manual research. Meanwhile,
Kenya's own census data already contains the two most important numbers
for this decision — **how many people currently lack electricity, and
where** — nobody has bothered to turn it into a ranked, actionable
shortlist. That's the first-principles gap this fills.

## How it works

1. **Electrification rate per county** — real constituency-level
   household electricity access percentages (2019 census data, published
   via Stats Kenya), averaged across each county's constituencies.
2. **Population per county** — real KNBS 2019 census and 2023 projection
   figures.
3. **Unelectrified population** = `population_2023 × (1 − electrification_rate)`
   — the actual number of people in that county without power today.
4. **Solar resource tier** — a real, literature-based estimate of solar
   irradiance (GHI) per county (see `data/county_solar_tier.csv` for full
   citations). Higher solar resource means cheaper, more productive
   mini-grid generation.
5. **Opportunity score** blends all three (market size, urgency, solar
   quality), each normalized 0–1, with adjustable weights — via CLI flags
   or the Streamlit sliders.
6. **Constituency-level ranking** — a separate, real ranking of all 296
   constituencies in the raw dataset by electrification access alone,
   for finding specific underserved sites within a promising county.

## Data sources (real, cited)

| File | Source |
|---|---|
| `data/constituency_access_raw.csv` | Stats Kenya, "Kenya: Access to Electricity by Constituency" — [statskenya.co.ke](https://statskenya.co.ke/at-stats-kenya/about/kenya-access-to-electricity-by-constituency-stats-kenya/82/), compiled from the 2019 Kenya Population and Housing Census |
| `data/county_population.csv` | KNBS 2019 Kenya Population and Housing Census (Vol. I) + 2023 population projections |
| `data/county_solar_tier.csv` | Real, literature-based regional solar estimate — see the file's header for full citations (a ScienceDirect spatial-variability study of Kenya's GHI, and Turkana County's own energy office data) |

## Running it

**Command line:**
```bash
pip install -r requirements.txt
python3 src/score_sites.py --top 15 --constituencies
```

Optional flags:
- `--w-unserved 0.5 --w-gap 0.3 --w-solar 0.2` — custom weights (don't need to sum to 1)
- `--top 47` — see the full county ranking
- `--constituencies` — also print/save the most underserved constituencies
- `--out output/my_ranking.csv` — custom output path

Output:
- `output/ranked_counties.csv` — full county ranking
- `output/ranked_constituencies.csv` — constituency ranking (with `--constituencies`)
- `output/top_counties_chart.png` — bar chart of the top counties

**Streamlit app** (move the weight sliders yourself, no code needed):
```bash
streamlit run app.py
```

## Honest limitations

- Electrification rate is an **unweighted mean** of constituencies within
  a county, not population-weighted. A true population-weighted rate
  needs constituency-level population for all 296 constituencies — KNBS
  publishes this (Volume II), but the one consolidated source found was
  blocked to automated access, and pulling all 296 rows one Wikipedia
  page at a time was outside this build's scope. Named honestly rather
  than silently skipped.
- The solar tier is a real, cited literature-based regional estimate, not
  a precise per-county Global Solar Atlas GIS pixel value.
- The constituency-level ranking is by access % alone (not
  population-weighted, for the same reason above) — it shows "most
  underserved," not "biggest market," at that granularity.
- Still no grid-distance, terrain, or existing competitor mini-grid data.
  Treat all output as a first-pass shortlist, not a final decision.

## Extending this further

- Get real constituency-level population (KNBS Volume II) to make both
  the county electrification rate and the constituency ranking properly
  population-weighted.
- Replace the literature-based solar tier with actual Global Solar Atlas
  GIS raster values per county centroid, using a GIS library.
- Add grid-distance (from KPLC's network data, if accessible) as a fourth
  scoring factor — closer to existing grid infrastructure usually means
  cheaper interconnection but also more competition.
