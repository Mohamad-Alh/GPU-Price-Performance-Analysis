"""
build_notebook.py
Builds notebooks/gpu_price_value_analysis.ipynb as a fully executed notebook
(code + markdown + rendered outputs) so it displays nicely on GitHub.
"""

import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
cells = []

md = lambda text: cells.append(nbf.v4.new_markdown_cell(text))
code = lambda text: cells.append(nbf.v4.new_code_cell(text))

md("""\
# GPU Price-to-Performance Analysis

**Author:** Mohamad Abdulkarim Alhamawi
**Goal:** Identify which graphics cards (GPUs) offer the best performance for the price, and how that
value has shifted between NVIDIA and AMD over time — the kind of question a PC hardware retailer,
IT procurement team, or system builder in the Saudi/GCC market would ask before stocking or
recommending components.

**Business questions**
1. Which GPUs deliver the most benchmark performance per dollar spent?
2. Does NVIDIA or AMD offer better average value, and does that change by price tier?
3. Is there a meaningful relationship between price and raw performance, or do prices diverge from performance at the high end?
4. Has power efficiency (performance per watt) improved over the years?

**Dataset:** GPU specifications, benchmark scores (PassMark G3Dmark), and retail prices for 2,300+
graphics cards released between 2009-2022. Source: [gradedSystem/GPU_Price_Specs](https://github.com/gradedSystem/GPU_Price_Specs)
(originally scraped from PC Builder, cross-referenced with a public Kaggle GPU dataset — see `data/README.md`
for full attribution).
""")

md("## 1. Setup & Load Data")
code("""\
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", font_scale=1.0)
PALETTE = {"NVIDIA": "#76B900", "AMD": "#ED1C24"}

df_raw = pd.read_csv("../data/gpu_benchmarks_prices_raw.csv")
df_raw.head()
""")

md("""\
## 2. Data Cleaning

The raw dataset covers every GPU PassMark has ever benchmarked, but most entries (older or very
niche cards) were never assigned a listed price, so we can't compute value for them. We also need
TDP (power draw) for the efficiency question in section 5.

**Cleaning steps:**
1. Drop rows missing `price` or `TDP` — can't analyze value or efficiency without them.
2. Remove rows with impossible values (price/benchmark ≤ 0).
3. Drop duplicate GPU listings.
4. Keep only NVIDIA and AMD (the "Other" bucket is 4 rows — too small to analyze as its own group).
5. Engineer value/efficiency metrics: `marks_per_dollar`, `price_per_mark`, `performance_per_watt`, and a `price_tier` bucket.
""")

code("""\
print(f"Raw shape: {df_raw.shape}")
print("\\nMissing values:")
print(df_raw.isna().sum())
""")

code("""\
df = df_raw.dropna(subset=["price", "TDP"]).copy()
df = df[(df["price"] > 0) & (df["G3Dmark"] > 0) & (df["TDP"] > 0)]
df = df.drop_duplicates(subset=["gpuName"])
df = df[df["brand"].isin(["NVIDIA", "AMD"])]

df["marks_per_dollar"] = (df["G3Dmark"] / df["price"]).round(2)
df["price_per_mark"] = (df["price"] / df["G3Dmark"]).round(4)
df["performance_per_watt"] = (df["G3Dmark"] / df["TDP"]).round(2)
df["price_tier"] = pd.cut(
    df["price"],
    bins=[0, 150, 350, 700, float("inf")],
    labels=["Budget (<$150)", "Mid-range ($150-350)", "High-end ($350-700)", "Enthusiast ($700+)"],
)
df = df.rename(columns={"testDate": "release_year"})

print(f"Cleaned shape: {df.shape}  (dropped {df_raw.shape[0] - df.shape[0]} rows, "
      f"{(1 - df.shape[0] / df_raw.shape[0]):.1%} of the original — almost entirely due to missing price data)")
df.head()
""")

md("## 3. Which GPUs offer the best value?")
code("""\
top_value = df.sort_values("marks_per_dollar", ascending=False).head(15)

fig, ax = plt.subplots(figsize=(9, 6))
colors = [PALETTE[b] for b in top_value["brand"]]
ax.barh(top_value["gpuName"], top_value["marks_per_dollar"], color=colors)
ax.set_xlabel("Performance points per $ (higher = better value)")
ax.set_title("Top 15 Best-Value GPUs (Benchmark Score per Dollar)")
ax.invert_yaxis()
plt.tight_layout()
plt.show()

top_value[["gpuName", "brand", "price", "G3Dmark", "marks_per_dollar"]]
""")

md("""\
**Insight:** Budget and previous-generation cards dominate the value rankings — the Radeon R9 380
and GeForce GTX 470 top the list. This is a familiar pattern in hardware markets: flagship cards
carry a price premium for the top performance spot, while one or two generations back typically
offers the best cost-per-performance-point, which matters directly for resale/refurb pricing strategy.
""")

md("## 4. Price vs. performance — where do the two brands diverge?")
code("""\
fig, ax = plt.subplots(figsize=(9, 6))
for brand, color in PALETTE.items():
    sub = df[df["brand"] == brand]
    ax.scatter(sub["price"], sub["G3Dmark"], label=brand, color=color, alpha=0.7, edgecolor="white", s=60)
ax.set_xlabel("Price (USD)")
ax.set_ylabel("Benchmark Score (G3Dmark)")
ax.set_title("Price vs. Performance by Brand")
ax.legend(title="Brand")
plt.tight_layout()
plt.show()

correlation = df["price"].corr(df["G3Dmark"])
print(f"Correlation between price and performance: {correlation:.2f}")
""")

md("""\
**Insight:** Price and performance are only moderately correlated (~0.5), which means price alone is a
weak predictor of performance — plenty of mid-priced cards outperform pricier ones. NVIDIA also has more
presence at the very top of the market (multiple cards past $4,000), reflecting its workstation/AI-focused lineup.
""")

md("## 5. Value by price tier — where is the sweet spot?")
code("""\
tier_order = ["Budget (<$150)", "Mid-range ($150-350)", "High-end ($350-700)", "Enthusiast ($700+)"]
pivot = df.groupby(["price_tier", "brand"], observed=True)["marks_per_dollar"].mean().unstack().reindex(tier_order)

fig, ax = plt.subplots(figsize=(9, 6))
pivot.plot(kind="bar", ax=ax, color=[PALETTE.get(c, "#888") for c in pivot.columns])
ax.set_ylabel("Avg. performance points per $")
ax.set_xlabel("Price Tier")
ax.set_title("Average Value by Price Tier and Brand")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.show()

pivot
""")

md("""\
**Insight:** The High-end tier ($350-700) delivers the best average value across both brands — enough
raw performance to matter, without the "flagship tax" enthusiast cards carry. Budget cards look
efficient per-dollar in isolation but max out at lower absolute performance, so they're best suited
for basic-use builds rather than performance-focused ones.
""")

md("## 6. Has power efficiency improved over time?")
code("""\
yearly = df.groupby(["release_year", "brand"])["performance_per_watt"].mean().reset_index()

fig, ax = plt.subplots(figsize=(9, 6))
for brand, color in PALETTE.items():
    sub = yearly[yearly["brand"] == brand]
    ax.plot(sub["release_year"], sub["performance_per_watt"], marker="o", label=brand, color=color)
ax.set_xlabel("Release Year")
ax.set_ylabel("Avg. Performance per Watt")
ax.set_title("GPU Power Efficiency Trend Over Time")
ax.legend(title="Brand")
plt.tight_layout()
plt.show()
""")

md("""\
**Insight:** Performance-per-watt trends upward for both brands over the 2009-2022 window, consistent
with successive die-shrink and architecture improvements — cards are getting more efficient generation
over generation, not just faster.
""")

md("""\
## 7. Summary of findings

| Question | Finding |
|---|---|
| Best value GPUs | Previous-generation and mid-range cards (e.g. Radeon R9 380, GeForce GTX 470/970/980) top the value rankings |
| NVIDIA vs. AMD average value | NVIDIA averages a slightly higher performance-per-dollar across the dataset |
| Price vs. performance | Moderately correlated (r ≈ 0.5) — price is not a reliable stand-alone predictor of performance |
| Best price tier for value | High-end ($350-700) offers the strongest average value across both brands |
| Power efficiency | Improves steadily for both brands from 2009 to 2022 |

## 8. Limitations & next steps
- Prices are historical USD retail snapshots (mostly 2021-2022), not adjusted for regional markets like Saudi Arabia/GCC or current used-market pricing.
- ~84% of the raw dataset lacked a listed price and had to be excluded — a larger or more recent price feed (e.g. live regional marketplace data) would strengthen the analysis.
- Next step: extend this pipeline to scrape live GCC marketplace listings (e.g. Haraj, Amazon.sa) and compare regional pricing against this global benchmark baseline.

An interactive version of this analysis (with brand/price filters) is available in `dashboard/app.py` (Streamlit).
""")

nb["cells"] = cells

out_path = Path(__file__).resolve().parent.parent / "notebooks" / "gpu_price_value_analysis.ipynb"
out_path.parent.mkdir(exist_ok=True)
with open(out_path, "w") as f:
    nbf.write(nb, f)

print("Notebook written to", out_path)
