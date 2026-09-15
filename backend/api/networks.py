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


@router.get("")
def get_networks(
    limit: int = Query(
        50,
        ge=1,
        le=500,
    ),
):

    df = load_csv(
        "suspicious_networks.csv"
    )

    if "network_risk_score" in df.columns:
        df = df.sort_values(
            "network_risk_score",
            ascending=False,
        )

    df = df.head(limit)

    return {
        "count": len(df),
        "networks": (
            df.where(
                pd.notnull(df),
                None,
            )
            .to_dict(
                orient="records"
            )
        ),
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
        "nodes": (
            nodes.where(
                pd.notnull(nodes),
                None,
            )
            .to_dict(
                orient="records"
            )
        ),
        "edges": (
            edges.where(
                pd.notnull(edges),
                None,
            )
            .to_dict(
                orient="records"
            )
        ),
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

    return (
        matches.head(1)
        .where(
            pd.notnull(
                matches.head(1)
            ),
            None,
        )
        .to_dict(
            orient="records"
        )[0]
    )
