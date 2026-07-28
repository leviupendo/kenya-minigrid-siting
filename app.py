"""
Mini-Grid Site Prioritization -- Streamlit App
================================================

Move the weight sliders yourself and watch the county ranking update live.
No coding needed -- built for a business analyst, not just a developer.

Run with:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st

from src.score_sites import load_data, score, rank_constituencies

st.set_page_config(page_title="Mini-Grid Site Prioritizer", layout="wide")

st.title("Mini-Grid Site Prioritization Tool")
st.caption(
    "Ranks Kenyan counties for new mini-grid investment using real KNBS "
    "population and electrification data, plus a literature-based solar "
    "resource tier. Adjust the weights in the sidebar to match your "
    "company's priorities."
)

st.sidebar.header("Scoring weights")
w_unserved = st.sidebar.slider("Market size (unelectrified population)", 0.0, 1.0, 0.4, 0.05)
w_gap = st.sidebar.slider("Urgency (access gap)", 0.0, 1.0, 0.4, 0.05)
w_solar = st.sidebar.slider("Solar resource quality", 0.0, 1.0, 0.2, 0.05)
top_n = st.sidebar.slider("Counties to show", 5, 47, 15)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Weights don't need to sum to 1 -- they're normalized automatically. "
    "Set solar to 0 to replicate the original two-factor model."
)

df, access_raw = load_data()
ranked = score(df, w_unserved, w_gap, w_solar)
top = ranked.head(top_n)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Top {top_n} counties")
    st.bar_chart(top.set_index("county")["opportunity_score"])

with col2:
    st.subheader("At a glance")
    st.metric("Counties covered", len(ranked))
    st.metric("Top county", top.iloc[0]["county"])
    st.metric("Its unelectrified population", f"{top.iloc[0]['unelectrified_population']:,}")

st.subheader("Full ranked table")
display_cols = ["county", "population_2023", "electrification_rate_pct",
                "unelectrified_population", "ghi_est_kwh_m2_day", "opportunity_score"]
st.dataframe(top[display_cols], use_container_width=True)

csv_bytes = ranked.to_csv(index=False).encode("utf-8")
st.download_button("Download full county ranking (CSV)", csv_bytes, "ranked_counties.csv", "text/csv")

st.markdown("---")
st.subheader("Most underserved constituencies (real data, finer detail)")
st.caption(
    "Ranked by electrification access alone -- NOT population-weighted "
    "(see README for why). Useful for identifying specific under-the-radar "
    "sites within a promising county."
)
n_const = st.slider("Constituencies to show", 10, 100, 30)
const_ranked = rank_constituencies(access_raw, top=n_const)
st.dataframe(const_ranked, use_container_width=True)

const_csv = const_ranked.to_csv(index=False).encode("utf-8")
st.download_button("Download constituency ranking (CSV)", const_csv, "ranked_constituencies.csv", "text/csv")

with st.expander("Data sources & honest limitations"):
    st.markdown("""
- **Population & electrification**: real KNBS 2019 census + 2023 projections, and Stats Kenya's constituency-level electrification table.
- **Solar tier**: a real, literature-based regional estimate (see `data/county_solar_tier.csv` for full citations) -- not a precise per-county satellite-pixel value.
- **Not yet population-weighted**: county electrification rate is an unweighted mean of its constituencies. A true population-weighted rate needs constituency-level population for all 296 constituencies, which KNBS publishes but which wasn't accessible to pull in full for this build.
- **Constituency ranking** uses access % alone, not population -- so it shows "most underserved," not "biggest market," at that level of detail.
- No grid-distance, terrain, or competitor mini-grid data yet. Treat this as a first-pass shortlist tool.
""")
