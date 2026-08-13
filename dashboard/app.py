"""
GPU Price-to-Performance Dashboard
-----------------------------------
Interactive Streamlit app to explore GPU value (performance per dollar)
by brand, price tier, and release year.

Run with:  streamlit run dashboard/app.py
"""

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="GPU Price-to-Performance Explorer", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "gpu_benchmarks_prices_clean.csv"
PALETTE = {"NVIDIA": "#76B900", "AMD": "#ED1C24"}


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


df = load_data()

st.title("🖥️ GPU Price-to-Performance Explorer")
st.caption(
    "Explore which graphics cards offer the best benchmark performance per dollar. "
    "Data: 383 GPUs (2009-2022), benchmark scores from PassMark, prices in USD."
)

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

brands = st.sidebar.multiselect(
    "Brand", options=sorted(df["brand"].unique()), default=sorted(df["brand"].unique())
)

price_min, price_max = int(df["price"].min()), int(df["price"].max())
price_range = st.sidebar.slider(
    "Price range (USD)", min_value=price_min, max_value=price_max, value=(price_min, min(1500, price_max))
)

year_min, year_max = int(df["release_year"].min()), int(df["release_year"].max())
year_range = st.sidebar.slider(
    "Release year", min_value=year_min, max_value=year_max, value=(year_min, year_max)
)

filtered = df[
    (df["brand"].isin(brands))
    & (df["price"].between(*price_range))
    & (df["release_year"].between(*year_range))
]

st.sidebar.markdown(f"**{len(filtered)}** GPUs match your filters")

# ---------------- KPI row ----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("GPUs shown", len(filtered))
col2.metric("Avg. price", f"${filtered['price'].mean():,.0f}" if len(filtered) else "—")
col3.metric("Avg. value (marks/$)", f"{filtered['marks_per_dollar'].mean():,.1f}" if len(filtered) else "—")
col4.metric("Best value pick", filtered.sort_values("marks_per_dollar", ascending=False)["gpuName"].iloc[0] if len(filtered) else "—")

st.divider()

# ---------------- Charts ----------------
left, right = st.columns(2)

with left:
    st.subheader("Top 10 best-value GPUs (in current filter)")
    top = filtered.sort_values("marks_per_dollar", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh(top["gpuName"], top["marks_per_dollar"], color=[PALETTE.get(b, "#888") for b in top["brand"]])
    ax.invert_yaxis()
    ax.set_xlabel("Performance points per $")
    st.pyplot(fig)

with right:
    st.subheader("Price vs. performance")
    fig, ax = plt.subplots(figsize=(6, 5))
    for brand, color in PALETTE.items():
        sub = filtered[filtered["brand"] == brand]
        ax.scatter(sub["price"], sub["G3Dmark"], label=brand, color=color, alpha=0.7, edgecolor="white")
    ax.set_xlabel("Price (USD)")
    ax.set_ylabel("Benchmark score (G3Dmark)")
    ax.legend()
    st.pyplot(fig)

st.subheader("Browse the filtered data")
st.dataframe(
    filtered[["gpuName", "brand", "release_year", "price", "G3Dmark", "marks_per_dollar", "performance_per_watt", "price_tier"]]
    .sort_values("marks_per_dollar", ascending=False)
    .reset_index(drop=True),
    use_container_width=True,
)

st.caption("Data source: PassMark GPU benchmarks & retail prices, via gradedSystem/GPU_Price_Specs (GitHub).")
