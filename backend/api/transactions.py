from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "transaction_intelligence.csv"
)


def load_data() -> pd.DataFrame:

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Transaction intelligence dataset not found.",
        )

    return pd.read_csv(DATA_FILE)


def clean_records(df: pd.DataFrame):

    return (
        df.replace(
            {
                pd.NA: None,
                float("nan"): None,
            }
        )
        .where(pd.notnull(df), None)
        .to_dict(orient="records")
    )


@router.get("")
def get_transactions(
    limit: int = Query(
        50,
        ge=1,
        le=500,
    ),
    risk_band: str | None = None,
):

    df = load_data()

    if risk_band:
        if "unified_risk_band" in df.columns:
            df = df[
                df["unified_risk_band"]
                .astype(str)
                .str.upper()
                == risk_band.upper()
            ]

    if "unified_risk_score" in df.columns:
        df = df.sort_values(
            "unified_risk_score",
            ascending=False,
        )

    df = df.head(limit)

    return {
        "count": len(df),
        "transactions": clean_records(df),
    }


@router.get("/{txn_id}")
def get_transaction(txn_id: str):

    df = load_data()

    if "txn_id" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="txn_id column missing.",
        )

    matches = df[
        df["txn_id"].astype(str)
        == str(txn_id)
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction not found: {txn_id}",
        )

    return clean_records(
        matches.head(1)
    )[0]
