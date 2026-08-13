"""
make_charts.py
--------------
Generates the analysis charts used in the README and notebook.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", font_scale=1.0)
PALETTE = {"NVIDIA": "#76B900", "AMD": "#ED1C24"}

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "gpu_benchmarks_prices_clean.csv"
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)

df = pd.read_csv(DATA)

# ---------------------------------------------------------------
# 1. Best value GPUs (top 15 by performance points per dollar)
# ---------------------------------------------------------------
top_value = df.sort_values("marks_per_dollar", ascending=False).head(15)
fig, ax = plt.subplots(figsize=(9, 6))
colors = [PALETTE[b] for b in top_value["brand"]]
ax.barh(top_value["gpuName"], top_value["marks_per_dollar"], color=colors)
ax.set_xlabel("Performance points per $ (higher = better value)")
ax.set_title("Top 15 Best-Value GPUs (Benchmark Score per Dollar)")
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(IMG / "top_value_gpus.png", dpi=150)
plt.close()

# ---------------------------------------------------------------
# 2. Price vs performance scatter
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 6))
for brand, color in PALETTE.items():
    sub = df[df["brand"] == brand]
    ax.scatter(sub["price"], sub["G3Dmark"], label=brand, color=color, alpha=0.7, edgecolor="white", s=60)
ax.set_xlabel("Price (USD)")
ax.set_ylabel("Benchmark Score (G3Dmark)")
ax.set_title("Price vs. Performance by Brand")
ax.legend(title="Brand")
plt.tight_layout()
plt.savefig(IMG / "price_vs_performance.png", dpi=150)
plt.close()

# ---------------------------------------------------------------
# 3. Average price by tier and brand
# ---------------------------------------------------------------
tier_order = ["Budget (<$150)", "Mid-range ($150-350)", "High-end ($350-700)", "Enthusiast ($700+)"]
pivot = df.groupby(["price_tier", "brand"], observed=True)["marks_per_dollar"].mean().unstack()
pivot = pivot.reindex(tier_order)
fig, ax = plt.subplots(figsize=(9, 6))
pivot.plot(kind="bar", ax=ax, color=[PALETTE.get(c, "#888") for c in pivot.columns])
ax.set_ylabel("Avg. performance points per $")
ax.set_xlabel("Price Tier")
ax.set_title("Average Value by Price Tier and Brand")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig(IMG / "value_by_tier.png", dpi=150)
plt.close()

# ---------------------------------------------------------------
# 4. Performance-per-watt efficiency over release years
# ---------------------------------------------------------------
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
plt.savefig(IMG / "efficiency_trend.png", dpi=150)
plt.close()

print("Saved 4 charts to", IMG)

# ---------------------------------------------------------------
# Print key stats used in the README
# ---------------------------------------------------------------
print("\n--- Key stats ---")
print("Best value GPU overall:", top_value.iloc[0]["gpuName"], top_value.iloc[0]["marks_per_dollar"])
print("NVIDIA avg marks_per_dollar:", df[df.brand == "NVIDIA"]["marks_per_dollar"].mean().round(2))
print("AMD avg marks_per_dollar:", df[df.brand == "AMD"]["marks_per_dollar"].mean().round(2))
print("Correlation price vs G3Dmark:", df["price"].corr(df["G3Dmark"]).round(2))
print("Best value tier:", pivot.mean(axis=1).idxmax())
