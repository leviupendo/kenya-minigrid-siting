"""
Mini-Grid Site Prioritization Tool
==================================

WHAT THIS DOES
--------------
Answers the real question for a solar mini-grid / off-grid energy company:
"Given limited capital, which Kenyan county -- or even which specific
constituency -- should we target next?"

METHOD (first-principles, not black-box)
-----------------------------------------
COUNTY LEVEL
1. electrification_rate_pct -> avg of real constituency-level household
   electricity access figures per county (Stats Kenya / KNBS 2019 census).
2. population_2023           -> real KNBS county population estimate.
3. unelectrified_population   -> population_2023 * (1 - electrification_rate/100)
4. opportunity_score          -> normalized blend of three factors:
   - unelectrified_population (bigger = more people to serve)
   - access_gap_pct = 100 - electrification_rate (higher = more urgent,
     less grid competition)
   - solar_score = normalized GHI tier (higher solar resource = cheaper,
     more productive mini-grid generation)
   All three are min-max normalized to 0-1 and blended with adjustable
   weights (CLI args or Streamlit sliders).

CONSTITUENCY LEVEL (new)
A separate, real ranking of the 296 constituencies in the raw dataset by
electrification access alone (lowest access = most underserved). This is
NOT population-weighted (see limitations) but is fully real data at a
finer grain than the county rollup.

DATA SOURCES (all real, all cited)
-----------------------------------
- data/constituency_access_raw.csv : household electricity access % by
  constituency, 2019 Kenya census, as published by Stats Kenya.
- data/county_population.csv : county population 2019 (census) and 2023
  (KNBS projection).
- data/county_solar_tier.csv : real, literature-based solar irradiance
  tier per county (see that file's header for full citations -- a
  ScienceDirect spatial-variability study and Turkana County's own energy
  office). This is an informed regional estimate, not a precise per-county
  satellite-pixel figure -- see limitations.

LIMITATIONS (stated honestly)
------------------------------
- County electrification rate is an *unweighted mean* of constituency
  figures, not population-weighted. Getting a real population-weighted
  rate needs constituency-level population for all 296 constituencies.
  KNBS publishes this (Volume II, "Constituency Population by Sex, Number
  of Households, Area and Density"), but the consolidated source is
  blocked to automated access from this environment, and pulling all 296
  rows one Wikipedia page at a time was outside this session's scope.
  This is a real, named gap -- not silently ignored.
- solar_est_kwh_m2_day is a literature-based tier estimate (see the data
  file's header), not a precise Global Solar Atlas GIS pixel value.
- The constituency-level ranking uses access_pct alone -- it is not
  population-weighted for the same reason as above, so it tells you
  "most underserved constituencies" but not "biggest constituency-level
  market."
- Still no grid-distance, terrain, or competitor mini-grid data.
  Treat all output as a first-pass shortlist, not a final decision.
"""

import argparse
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_data(data_dir="data"):
    access_raw = pd.read_csv(f"{data_dir}/constituency_access_raw.csv", comment="#")
    county_access = (
        access_raw.groupby("county")["access_pct"]
        .mean()
        .reset_index()
        .rename(columns={"access_pct": "electrification_rate_pct"})
    )
    pop = pd.read_csv(f"{data_dir}/county_population.csv")
    solar = pd.read_csv(f"{data_dir}/county_solar_tier.csv", comment="#")

    df = pop.merge(county_access, on="county", how="inner").merge(solar, on="county", how="left")
    return df, access_raw


def score(df, w_unserved=0.4, w_access_gap=0.4, w_solar=0.2):
    df = df.copy()
    df["unelectrified_population"] = (
        df["population_2023"] * (1 - df["electrification_rate_pct"] / 100)
    ).round(0).astype(int)
    df["access_gap_pct"] = (100 - df["electrification_rate_pct"]).round(1)

    def norm(col):
        return (df[col] - df[col].min()) / (df[col].max() - df[col].min())

    df["_unserved_norm"] = norm("unelectrified_population")
    df["_gap_norm"] = norm("access_gap_pct")
    df["_solar_norm"] = norm("ghi_est_kwh_m2_day")

    total_w = w_unserved + w_access_gap + w_solar
    if total_w == 0:
        total_w = 1  # avoid div by zero; scores will just be 0
    df["opportunity_score"] = (
        (w_unserved * df["_unserved_norm"]
         + w_access_gap * df["_gap_norm"]
         + w_solar * df["_solar_norm"]) / total_w
    ).round(3)

    df = df.drop(columns=["_unserved_norm", "_gap_norm", "_solar_norm"])
    return df.sort_values("opportunity_score", ascending=False).reset_index(drop=True)


def rank_constituencies(access_raw, top=30):
    """Real constituency-level ranking by lowest electrification access.
    NOT population-weighted -- see module limitations."""
    return access_raw.sort_values("access_pct", ascending=True).reset_index(drop=True).head(top)


def main():
    parser = argparse.ArgumentParser(description="Rank Kenyan counties/constituencies for mini-grid siting")
    parser.add_argument("--top", type=int, default=15, help="Number of counties to show")
    parser.add_argument("--w-unserved", type=float, default=0.4, help="Weight: unelectrified population size")
    parser.add_argument("--w-gap", type=float, default=0.4, help="Weight: access gap / underservedness")
    parser.add_argument("--w-solar", type=float, default=0.2, help="Weight: solar resource quality")
    parser.add_argument("--constituencies", action="store_true",
                         help="Also print the most underserved constituencies")
    parser.add_argument("--out", default="output/ranked_counties.csv")
    args = parser.parse_args()

    df, access_raw = load_data()
    ranked = score(df, args.w_unserved, args.w_gap, args.w_solar)
    ranked.to_csv(args.out, index=False)

    cols = ["county", "population_2023", "electrification_rate_pct",
            "unelectrified_population", "ghi_est_kwh_m2_day", "opportunity_score"]
    print(f"\nTop {args.top} counties for new mini-grid investment (real KNBS + solar-literature data):\n")
    print(ranked[cols].head(args.top).to_string(index=False))
    print(f"\nFull ranked list saved to {args.out}")

    top_n = ranked.head(args.top)
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(top_n["county"][::-1], top_n["opportunity_score"][::-1], color="#2E8B57")
    ax.set_xlabel("Opportunity score (0-1)")
    ax.set_title(f"Top {args.top} Kenyan counties for mini-grid investment\n"
                 "(real population + electrification + solar-tier data)")
    for bar, rate in zip(bars, top_n["electrification_rate_pct"][::-1]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{rate:.0f}% electrified", va="center", fontsize=8, color="#444")
    plt.tight_layout()
    chart_path = "output/top_counties_chart.png"
    plt.savefig(chart_path, dpi=150)
    print(f"Chart saved to {chart_path}")

    if args.constituencies:
        const_ranked = rank_constituencies(access_raw, top=30)
        const_out = "output/ranked_constituencies.csv"
        const_ranked.to_csv(const_out, index=False)
        print(f"\nTop 30 most underserved constituencies (real data, NOT population-weighted):\n")
        print(const_ranked.to_string(index=False))
        print(f"\nFull constituency ranking saved to {const_out}")


if __name__ == "__main__":
    main()
