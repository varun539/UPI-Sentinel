from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter()


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "merchant_intelligence.csv"
)


def load_data():
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Merchant intelligence dataset not found.",
        )

    return pd.read_csv(DATA_FILE)


def records(df):
    """
    Convert dataframe rows into JSON-safe dictionaries.

    Pandas NaN values are converted to Python None so that
    FastAPI can serialize the response as valid JSON.
    """

    safe_df = (
        df.astype(object)
        .where(pd.notnull(df), None)
    )

    return safe_df.to_dict(
        orient="records"
    )


@router.get("")
def get_merchants(
    limit: int = Query(
        50,
        ge=1,
        le=500,
    ),
    risk_band: str | None = None,
):
    df = load_data()

    if risk_band:
        df = df[
            df[
                "unified_merchant_risk_band"
            ]
            .astype(str)
            .str.upper()
            == risk_band.upper()
        ]

    df = df.sort_values(
        "unified_merchant_risk_score",
        ascending=False,
    )

    df = df.head(limit)

    return {
        "count": len(df),
        "merchants": records(df),
    }


@router.get("/{merchant_id}")
def get_merchant(
    merchant_id: str
):
    df = load_data()

    matches = df[
        df["merchant_id"].astype(str)
        == str(merchant_id)
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Merchant not found: "
                f"{merchant_id}"
            ),
        )

    return records(
        matches.head(1)
    )[0]