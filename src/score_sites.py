"""
Mini-Grid Site Prioritization Tool
==================================

WHAT THIS DOES
--------------
Answers one real question for a solar mini-grid / off-grid energy company:
"Given limited capital, which Kenyan county should we target next?"

METHOD (first-principles, not black-box)
-----------------------------------------
1. electrification_rate_pct  -> avg of real constituency-level household
   electricity access figures per county (Stats Kenya / KNBS 2019 census).
2. population_2023            -> real KNBS county population estimate.
3. unelectrified_population    -> population_2023 * (1 - electrification_rate/100)
   This is the actual number of people a mini-grid company could realistically
   serve in that county -- the true addressable market, not a guess.
4. opportunity_score           -> normalized blend of:
      - unelectrified_population (bigger = more people to serve = more revenue potential)
      - (100 - electrification_rate) (lower current access = less competition
        from the existing grid, higher urgency)
   Both are min-max normalized to 0-1 and averaged with equal weight by default.
   Weights are exposed as CLI args so you can tune the trade-off between
   "serve the most people" vs "serve the most underserved people".

DATA SOURCES (all real, all cited)
-----------------------------------
- data/constituency_access_raw.csv : household electricity access % by
  constituency, 2019 Kenya census, as published by Stats Kenya
  (https://statskenya.co.ke) drawing on KNBS 2019 census + CRA county
  factsheets.
- data/county_population.csv : county population 2019 (census) and 2023
  (KNBS projection), compiled from KNBS 2019 Kenya Population and Housing
  Census, Volume I & II.

LIMITATIONS (stated honestly)
------------------------------
- County electrification rate here is the *unweighted mean* of available
  constituency figures, not a population-weighted rate -- a reasonable proxy
  given constituency-level population wasn't merged in, but a real production
  version should weight by constituency population.
- This does not include grid-distance, terrain, solar irradiance, or existing
  competitor mini-grids -- all of which a real site-selection team would add.
  Treat the output as a first-pass shortlist, not a final investment decision.
"""

import argparse
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_data(data_dir="data"):
    access_raw = pd.read_csv(f"{data_dir}/constituency_access_raw.csv")
    county_access = (
        access_raw.groupby("county")["access_pct"]
        .mean()
        .reset_index()
        .rename(columns={"access_pct": "electrification_rate_pct"})
    )

    pop = pd.read_csv(f"{data_dir}/county_population.csv")

    df = pop.merge(county_access, on="county", how="inner")
    return df


def score(df, w_unserved=0.5, w_access_gap=0.5):
    df = df.copy()
    df["unelectrified_population"] = (
        df["population_2023"] * (1 - df["electrification_rate_pct"] / 100)
    ).round(0).astype(int)
    df["access_gap_pct"] = (100 - df["electrification_rate_pct"]).round(1)

    def norm(col):
        return (df[col] - df[col].min()) / (df[col].max() - df[col].min())

    df["_unserved_norm"] = norm("unelectrified_population")
    df["_gap_norm"] = norm("access_gap_pct")

    df["opportunity_score"] = (
        w_unserved * df["_unserved_norm"] + w_access_gap * df["_gap_norm"]
    ).round(3)

    df = df.drop(columns=["_unserved_norm", "_gap_norm"])
    return df.sort_values("opportunity_score", ascending=False).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Rank Kenyan counties for mini-grid siting")
    parser.add_argument("--top", type=int, default=15, help="Number of counties to show")
    parser.add_argument("--w-unserved", type=float, default=0.5,
                         help="Weight for unelectrified population size (0-1)")
    parser.add_argument("--w-gap", type=float, default=0.5,
                         help="Weight for access gap / underservedness (0-1)")
    parser.add_argument("--out", default="output/ranked_counties.csv",
                         help="Where to save full ranked CSV")
    args = parser.parse_args()

    df = load_data()
    ranked = score(df, args.w_unserved, args.w_gap)

    ranked.to_csv(args.out, index=False)

    cols = ["county", "population_2023", "electrification_rate_pct",
            "unelectrified_population", "opportunity_score"]
    print(f"\nTop {args.top} counties for new mini-grid investment (real KNBS data):\n")
    print(ranked[cols].head(args.top).to_string(index=False))
    print(f"\nFull ranked list saved to {args.out}")

    # Chart: top counties by opportunity score, colored by electrification rate
    top_n = ranked.head(args.top)
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(top_n["county"][::-1], top_n["opportunity_score"][::-1],
                    color="#2E8B57")
    ax.set_xlabel("Opportunity score (0-1)")
    ax.set_title(f"Top {args.top} Kenyan counties for mini-grid investment\n"
                 "(real KNBS population + electrification data)")
    for bar, rate in zip(bars, top_n["electrification_rate_pct"][::-1]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{rate:.0f}% electrified", va="center", fontsize=8, color="#444")
    plt.tight_layout()
    chart_path = "output/top_counties_chart.png"
    plt.savefig(chart_path, dpi=150)
    print(f"Chart saved to {chart_path}")


if __name__ == "__main__":
    main()
