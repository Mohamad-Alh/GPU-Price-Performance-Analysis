"""
clean_data.py
--------------
Cleans the raw GPU benchmark + price dataset and saves an analysis-ready CSV.

Raw data source: gradedSystem/GPU_Price_Specs (GitHub), originally scraped
from PC Builder (pcbuilder.net) and cross-referenced with a Kaggle GPU
price dataset. See data/README.md for full attribution.
"""

import pandas as pd
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "gpu_benchmarks_prices_raw.csv"
CLEAN_PATH = Path(__file__).resolve().parent.parent / "data" / "gpu_benchmarks_prices_clean.csv"


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Drop rows missing the two fields we can't analyze without: price and TDP
    df = df.dropna(subset=["price", "TDP"])

    # 2. Remove impossible / placeholder values
    df = df[(df["price"] > 0) & (df["G3Dmark"] > 0) & (df["TDP"] > 0)]

    # 3. Drop duplicate GPU listings, keeping the first (most complete) record
    df = df.drop_duplicates(subset=["gpuName"])

    # 4. Standardize brand labels and drop the tiny "Other" bucket (4 rows,
    #    not enough to analyze as its own group)
    df = df[df["brand"].isin(["NVIDIA", "AMD"])]

    # 5. Feature engineering
    df["price_per_mark"] = (df["price"] / df["G3Dmark"]).round(4)          # $ per performance point (lower = better value)
    df["marks_per_dollar"] = (df["G3Dmark"] / df["price"]).round(2)        # performance points per $ (higher = better value)
    df["performance_per_watt"] = (df["G3Dmark"] / df["TDP"]).round(2)      # efficiency
    df["price_tier"] = pd.cut(
        df["price"],
        bins=[0, 150, 350, 700, float("inf")],
        labels=["Budget (<$150)", "Mid-range ($150-350)", "High-end ($350-700)", "Enthusiast ($700+)"],
    )

    df = df.rename(columns={"testDate": "release_year"})
    df = df[
        [
            "gpuName", "brand", "release_year", "category", "price", "price_tier",
            "G3Dmark", "TDP", "price_per_mark", "marks_per_dollar", "performance_per_watt",
        ]
    ].reset_index(drop=True)

    return df


def main():
    raw = load_raw()
    print(f"Raw dataset: {raw.shape[0]} rows, {raw.shape[1]} columns")

    cleaned = clean(raw)
    print(f"Cleaned dataset: {cleaned.shape[0]} rows, {cleaned.shape[1]} columns")
    print(f"Dropped {raw.shape[0] - cleaned.shape[0]} rows "
          f"({(1 - cleaned.shape[0] / raw.shape[0]):.1%}) — mostly missing price/TDP data")

    cleaned.to_csv(CLEAN_PATH, index=False)
    print(f"Saved cleaned data to {CLEAN_PATH}")


if __name__ == "__main__":
    main()
