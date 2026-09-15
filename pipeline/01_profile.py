from pathlib import Path
import json
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def profile_dataframe(df: pd.DataFrame, name: str) -> dict:
    columns = []

    for column in df.columns:
        series = df[column]

        columns.append({
            "name": column,
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 2),
            "unique_count": int(series.nunique(dropna=True)),
            "duplicate_value_count": int(series.duplicated().sum()),
        })

    return {
        "dataset": name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns_detail": columns,
    }


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def load_json(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return pd.json_normalize(data)


def main():
    profiles = []

    csv_files = [
        "track1_upi_transactions.csv",
        "track1_kyc_records.csv",
        "track1_merchants_master.csv",
    ]

    for filename in csv_files:
        path = RAW_DIR / filename

        print(f"\nLoading {filename}...")

        df = load_csv(path)

        profile = profile_dataframe(df, filename)
        profiles.append(profile)

        print(
            f"Rows: {profile['rows']:,} | "
            f"Columns: {profile['columns']} | "
            f"Duplicates: {profile['duplicate_rows']:,}"
        )

    json_path = RAW_DIR / "track1_chargebacks.json"

    print(f"\nLoading {json_path.name}...")

    chargebacks = load_json(json_path)

    profile = profile_dataframe(
        chargebacks,
        json_path.name
    )

    profiles.append(profile)

    print(
        f"Rows: {profile['rows']:,} | "
        f"Columns: {profile['columns']} | "
        f"Duplicates: {profile['duplicate_rows']:,}"
    )

    output_path = REPORT_DIR / "raw_data_profile.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(profiles, file, indent=2)

    print("\n" + "=" * 60)
    print("RAW DATA PROFILING COMPLETE")
    print("=" * 60)
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()