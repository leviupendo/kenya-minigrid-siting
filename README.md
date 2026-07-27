# Mini-Grid Site Prioritization Tool

A small, real-data tool that answers one concrete question for a solar
mini-grid / off-grid energy company operating in Kenya:

> **"Given limited capital, which county should we invest in next?"**

Instead of guessing or relying on anecdote, this ranks all 47 Kenyan
counties by an **opportunity score** built from real government data.

## Why this exists

Off-grid solar and mini-grid companies decide where to build using a mix
of intuition, sales-team anecdotes, and slow manual research. Meanwhile,
Kenya's own census and county fact-sheet data already contains the two
most important numbers for this decision — **how many people currently
lack electricity, and where** — nobody has bothered to turn it into a
ranked, actionable shortlist. That's the first-principles gap this fills.

## How it works

1. **Electrification rate per county** is computed from real
   constituency-level household electricity access percentages (2019
   census data, published via Stats Kenya / KNBS / Commission on Revenue
   Allocation county fact sheets). We average all constituencies within
   each county.
2. **Population per county** comes from the real KNBS 2019 census and
   2023 projection figures.
3. **Unelectrified population** = `population_2023 × (1 − electrification_rate)`
   — the actual number of people in that county without power today.
4. **Opportunity score** blends (a) how many unelectrified people live
   there (market size) and (b) how far behind the county is on access
   (urgency / less grid competition), each normalized 0–1 and averaged.
   Weights are adjustable via CLI flags.

## Data sources (real, cited)

| File | Source |
|---|---|
| `data/constituency_access_raw.csv` | Stats Kenya, "Kenya: Access to Electricity by Constituency," drawing on KNBS 2019 census + CRA County Fact Sheets (3rd ed.) |
| `data/county_population.csv` | KNBS 2019 Kenya Population and Housing Census (Vol. I & II) + 2023 projections |

## Running it

```bash
pip install -r requirements.txt
python3 src/score_sites.py --top 15
```

Optional flags:
- `--w-unserved 0.7 --w-gap 0.3` — weight toward raw market size over urgency
- `--top 47` — see the full ranking
- `--out output/my_ranking.csv` — custom output path

Output:
- `output/ranked_counties.csv` — full ranked table
- `output/top_counties_chart.png` — bar chart of the top counties

## Honest limitations

- Electrification rate is an **unweighted mean** of constituencies within
  a county, not population-weighted. A production version should weight
  by constituency population for more accuracy.
- Doesn't yet include grid-distance, terrain, solar irradiance, or
  existing mini-grid competitors. Real site selection needs all of these.
  Treat this as a first-pass shortlist generator, not a final decision tool.

## Extending this (natural next steps)

- Add population-weighted electrification rates (needs sub-county
  population, also published by KNBS).
- Pull in solar irradiance data (NASA POWER / Global Solar Atlas) as a
  third scoring factor.
- Add a Streamlit front-end so a non-technical business user can move the
  weight sliders themselves.
- Package the constituency-level (not just county-level) ranking, since
  the real underlying data is granular enough to go much more local.
