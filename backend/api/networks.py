from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter()


BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)


def load_csv(filename):
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Network dataset not found: {filename}",
        )

    return pd.read_csv(path)


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
def get_networks(
    limit: int = Query(
        250,
        ge=1,
        le=500,
    ),
    risk_band: str | None = None,
):
    df = load_csv(
        "suspicious_networks.csv"
    )

    # Filter the complete candidate dataset first.
    # This ensures Medium/Low networks are available
    # instead of only filtering the top overall networks.
    if risk_band:
        if "risk_band" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail="risk_band column missing.",
            )

        df = df[
            df["risk_band"]
            .astype(str)
            .str.upper()
            == risk_band.upper()
        ]

    # Highest-risk networks first.
    if "network_risk_score" in df.columns:
        df = df.sort_values(
            "network_risk_score",
            ascending=False,
        )

    df = df.head(limit)

    return {
        "count": len(df),
        "networks": records(df),
    }


@router.get("/graph")
def get_graph(
    limit: int = Query(
        5000,
        ge=1,
        le=20000,
    ),
):
    edges = load_csv(
        "fraud_graph_edges.csv"
    )

    nodes = load_csv(
        "fraud_graph_nodes.csv"
    )

    edges = edges.head(limit)

    return {
        "nodes": records(nodes),
        "edges": records(edges),
    }


@router.get("/{component_id}")
def get_network(
    component_id: int
):
    df = load_csv(
        "suspicious_networks.csv"
    )

    if "component_id" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="component_id column missing.",
        )

    matches = df[
        pd.to_numeric(
            df["component_id"],
            errors="coerce",
        )
        == component_id
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Network component not found: "
                f"{component_id}"
            ),
        )

    return records(
        matches.head(1)
    )[0]