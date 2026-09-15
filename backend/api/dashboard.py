from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def load_csv(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Processed dataset not found: {filename}",
        )

    return pd.read_csv(path)


@router.get("/summary")
def dashboard_summary():

    tx = load_csv(
        "transaction_intelligence.csv"
    )

    users = load_csv(
        "user_intelligence.csv"
    )

    merchants = load_csv(
        "merchant_intelligence.csv"
    )

    queue = load_csv(
        "investigation_queue.csv"
    )

    summary = {
        "transactions": len(tx),
        "users": len(users),
        "merchants": len(merchants),
        "investigation_candidates": len(queue),
    }

    if "unified_risk_score" in tx.columns:
        summary["average_transaction_risk"] = round(
            float(tx["unified_risk_score"].mean()),
            2,
        )

    if "unified_user_risk_score" in users.columns:
        summary["average_user_risk"] = round(
            float(users["unified_user_risk_score"].mean()),
            2,
        )

    if "unified_merchant_risk_score" in merchants.columns:
        summary["average_merchant_risk"] = round(
            float(
                merchants[
                    "unified_merchant_risk_score"
                ].mean()
            ),
            2,
        )

    return summary


@router.get("/risk-distribution")
def risk_distribution():

    tx = load_csv(
        "transaction_intelligence.csv"
    )

    users = load_csv(
        "user_intelligence.csv"
    )

    merchants = load_csv(
        "merchant_intelligence.csv"
    )

    result = {
        "transactions": {},
        "users": {},
        "merchants": {},
    }

    if "unified_risk_band" in tx.columns:
        result["transactions"] = {
            str(k): int(v)
            for k, v in
            tx["unified_risk_band"]
            .value_counts()
            .to_dict()
            .items()
        }

    if "unified_user_risk_band" in users.columns:
        result["users"] = {
            str(k): int(v)
            for k, v in
            users["unified_user_risk_band"]
            .value_counts()
            .to_dict()
            .items()
        }

    if "unified_merchant_risk_band" in merchants.columns:
        result["merchants"] = {
            str(k): int(v)
            for k, v in
            merchants["unified_merchant_risk_band"]
            .value_counts()
            .to_dict()
            .items()
        }

    return result
