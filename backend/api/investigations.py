from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "investigation_queue.csv"
)


def load_data():

    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Investigation queue not found.",
        )

    return pd.read_csv(DATA_FILE)


@router.get("")
def get_investigations(
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    entity_type: str | None = None,
):

    df = load_data()

    if entity_type:
        df = df[
            df["entity_type"]
            .astype(str)
            .str.upper()
            == entity_type.upper()
        ]

    if "risk_score" in df.columns:
        df = df.sort_values(
            "risk_score",
            ascending=False,
        )

    df = df.head(limit)

    return {
        "count": len(df),
        "investigations": (
            df.where(
                pd.notnull(df),
                None,
            )
            .to_dict(
                orient="records"
            )
        ),
    }


@router.get("/stats")
def investigation_stats():

    df = load_data()

    result = {
        "total": len(df),
    }

    if "entity_type" in df.columns:
        result["by_entity_type"] = {
            str(k): int(v)
            for k, v in
            df["entity_type"]
            .value_counts()
            .to_dict()
            .items()
        }

    if "risk_band" in df.columns:
        result["by_risk_band"] = {
            str(k): int(v)
            for k, v in
            df["risk_band"]
            .value_counts()
            .to_dict()
            .items()
        }

    return result
