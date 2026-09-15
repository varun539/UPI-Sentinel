"""
UPI SENTINEL — STAGE 08
Unified Fraud Intelligence

Combines:
- Rule-based transaction risk
- User risk
- Merchant risk
- ML anomaly detection
- Fraud graph / network intelligence

Produces investigation-ready transaction, user and merchant tables.

IMPORTANT:
Scores are risk indicators, NOT calibrated probabilities
and NOT proof of confirmed fraud.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================================
# CONFIG
# ======================================================================

BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------
# INPUTS
# ----------------------------------------------------------------------

TRANSACTION_INPUT = PROCESSED_DIR / "transaction_ml_anomalies.csv"
USER_INPUT = PROCESSED_DIR / "user_ml_anomalies.csv"
MERCHANT_INPUT = PROCESSED_DIR / "merchant_ml_anomalies.csv"

GRAPH_EDGES_INPUT = PROCESSED_DIR / "fraud_graph_edges.csv"
GRAPH_NODES_INPUT = PROCESSED_DIR / "fraud_graph_nodes.csv"
SUSPICIOUS_NETWORK_INPUT = PROCESSED_DIR / "suspicious_networks.csv"


# ----------------------------------------------------------------------
# OUTPUTS
# ----------------------------------------------------------------------

TRANSACTION_OUTPUT = PROCESSED_DIR / "transaction_intelligence.csv"
USER_OUTPUT = PROCESSED_DIR / "user_intelligence.csv"
MERCHANT_OUTPUT = PROCESSED_DIR / "merchant_intelligence.csv"
INVESTIGATION_QUEUE_OUTPUT = (
    PROCESSED_DIR / "investigation_queue.csv"
)

REPORT_OUTPUT = REPORT_DIR / "unified_intelligence_report.json"


# ======================================================================
# HELPERS
# ======================================================================

def numeric(
    df: pd.DataFrame,
    column: str,
    default: float = 0.0,
) -> pd.Series:
    """Safely retrieve a numeric column."""

    if column not in df.columns:
        return pd.Series(
            default,
            index=df.index,
            dtype=float,
        )

    return pd.to_numeric(
        df[column],
        errors="coerce",
    ).fillna(default)


def string(
    df: pd.DataFrame,
    column: str,
    default: str = "",
) -> pd.Series:
    """Safely retrieve a string column."""

    if column not in df.columns:
        return pd.Series(
            default,
            index=df.index,
            dtype="string",
        )

    return (
        df[column]
        .astype("string")
        .fillna(default)
    )


def normalize_id(
    series: pd.Series,
    remove_hyphen: bool = False,
) -> pd.Series:
    """Canonicalize entity IDs."""

    result = (
        series
        .astype("string")
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", "", regex=True)
    )

    if remove_hyphen:
        result = result.str.replace(
            "-",
            "",
            regex=False,
        )

    return result


def risk_band(
    score: pd.Series,
) -> pd.Series:
    """Convert 0–100 risk score into investigator-friendly bands."""

    return pd.Series(
        np.select(
            [
                score > 75,
                score > 50,
                score > 25,
            ],
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
            ],
            default="LOW",
        ),
        index=score.index,
        dtype="string",
    )


def minmax_100(
    series: pd.Series,
) -> pd.Series:
    """Scale arbitrary values to 0–100."""

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).fillna(0)

    minimum = values.min()
    maximum = values.max()

    if maximum == minimum:
        return pd.Series(
            0.0,
            index=values.index,
        )

    return (
        (values - minimum)
        / (maximum - minimum)
        * 100
    ).clip(0, 100)


def ensure_column(
    df: pd.DataFrame,
    column: str,
    default=0,
) -> pd.DataFrame:
    """Create a missing column without breaking the pipeline."""

    if column not in df.columns:
        df[column] = default

    return df


# ======================================================================
# LOAD
# ======================================================================

def load_data():

    print("Loading intelligence inputs...")

    transactions = pd.read_csv(
        TRANSACTION_INPUT
    )

    users = pd.read_csv(
        USER_INPUT
    )

    merchants = pd.read_csv(
        MERCHANT_INPUT
    )

    graph_edges = pd.read_csv(
        GRAPH_EDGES_INPUT
    )

    graph_nodes = pd.read_csv(
        GRAPH_NODES_INPUT
    )

    suspicious_networks = pd.read_csv(
        SUSPICIOUS_NETWORK_INPUT
    )

    print(
        f"✓ Transactions: "
        f"{len(transactions):,}"
    )

    print(
        f"✓ Users: "
        f"{len(users):,}"
    )

    print(
        f"✓ Merchants: "
        f"{len(merchants):,}"
    )

    print(
        f"✓ Graph edges: "
        f"{len(graph_edges):,}"
    )

    print(
        f"✓ Graph nodes: "
        f"{len(graph_nodes):,}"
    )

    print(
        f"✓ Suspicious networks: "
        f"{len(suspicious_networks):,}"
    )

    return (
        transactions,
        users,
        merchants,
        graph_edges,
        graph_nodes,
        suspicious_networks,
    )


# ======================================================================
# NETWORK INTELLIGENCE
# ======================================================================

def build_network_lookup(
    graph_edges: pd.DataFrame,
    graph_nodes: pd.DataFrame,
    suspicious_networks: pd.DataFrame,
):

    print("\nBuilding network intelligence...")

    # --------------------------------------------------------------
    # Edge lookup
    # --------------------------------------------------------------

    edges = graph_edges.copy()

    if "user_id" not in edges.columns:
        edges["user_id"] = ""

    if "merchant_id" not in edges.columns:
        edges["merchant_id"] = ""

    edges["user_id"] = normalize_id(
        edges["user_id"]
    )

    edges["merchant_id"] = normalize_id(
        edges["merchant_id"],
        remove_hyphen=True,
    )

    edges["relationship_risk_score"] = numeric(
        edges,
        "relationship_risk_score",
    )

    edges["transaction_count"] = numeric(
        edges,
        "transaction_count",
    )

    edges["total_amount"] = numeric(
        edges,
        "total_amount",
    )

    edges["chargeback_count"] = numeric(
        edges,
        "chargeback_count",
    )

    # --------------------------------------------------------------
    # User network statistics
    # --------------------------------------------------------------

    user_network = (
        edges.groupby(
            "user_id",
            as_index=False,
        )
        .agg(
            network_merchant_count=(
                "merchant_id",
                "nunique",
            ),
            network_transaction_count=(
                "transaction_count",
                "sum",
            ),
            network_total_amount=(
                "total_amount",
                "sum",
            ),
            network_chargeback_count=(
                "chargeback_count",
                "sum",
            ),
            avg_relationship_risk=(
                "relationship_risk_score",
                "mean",
            ),
            max_relationship_risk=(
                "relationship_risk_score",
                "max",
            ),
        )
    )

    user_network[
        "network_chargeback_rate"
    ] = np.where(
        user_network[
            "network_transaction_count"
        ] > 0,

        user_network[
            "network_chargeback_count"
        ]
        / user_network[
            "network_transaction_count"
        ],

        0,
    )

    # --------------------------------------------------------------
    # Merchant network statistics
    # --------------------------------------------------------------

    merchant_network = (
        edges.groupby(
            "merchant_id",
            as_index=False,
        )
        .agg(
            network_user_count=(
                "user_id",
                "nunique",
            ),
            network_transaction_count=(
                "transaction_count",
                "sum",
            ),
            network_total_amount=(
                "total_amount",
                "sum",
            ),
            network_chargeback_count=(
                "chargeback_count",
                "sum",
            ),
            avg_relationship_risk=(
                "relationship_risk_score",
                "mean",
            ),
            max_relationship_risk=(
                "relationship_risk_score",
                "max",
            ),
        )
    )

    merchant_network[
        "network_chargeback_rate"
    ] = np.where(
        merchant_network[
            "network_transaction_count"
        ] > 0,

        merchant_network[
            "network_chargeback_count"
        ]
        / merchant_network[
            "network_transaction_count"
        ],

        0,
    )

    # --------------------------------------------------------------
    # Graph node information
    # --------------------------------------------------------------

    nodes = graph_nodes.copy()

    if "entity_id" not in nodes.columns:
        nodes["entity_id"] = ""

    nodes["entity_id"] = normalize_id(
        nodes["entity_id"]
    )

    if "node_type" not in nodes.columns:
        nodes["node_type"] = ""

    node_columns = [
        "entity_id",
        "node_type",
        "degree",
        "component_id",
        "network_activity_score",
        "avg_relationship_risk",
    ]

    available_node_columns = [
        col
        for col in node_columns
        if col in nodes.columns
    ]

    nodes = nodes[
        available_node_columns
    ].copy()

    nodes = nodes.rename(
        columns={
            "avg_relationship_risk":
                "graph_avg_relationship_risk",
        }
    )

    # --------------------------------------------------------------
    # Suspicious component IDs
    # --------------------------------------------------------------

    suspicious_components = set()

    if not suspicious_networks.empty:
        if "component_id" in suspicious_networks.columns:

            suspicious_components = set(
                pd.to_numeric(
                    suspicious_networks[
                        "component_id"
                    ],
                    errors="coerce",
                )
                .dropna()
                .astype(int)
                .tolist()
            )

    nodes["suspicious_component_flag"] = (
        pd.to_numeric(
            nodes.get(
                "component_id",
                0,
            ),
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
        .isin(
            suspicious_components
        )
        .astype(int)
    )

    # --------------------------------------------------------------
    # Separate user and merchant node data
    # --------------------------------------------------------------

    user_nodes = nodes[
        nodes["node_type"]
        == "USER"
    ].copy()

    merchant_nodes = nodes[
        nodes["node_type"]
        == "MERCHANT"
    ].copy()

    print(
        f"✓ User network records: "
        f"{len(user_network):,}"
    )

    print(
        f"✓ Merchant network records: "
        f"{len(merchant_network):,}"
    )

    print(
        f"✓ Suspicious graph components: "
        f"{len(suspicious_components):,}"
    )

    return (
        user_network,
        merchant_network,
        user_nodes,
        merchant_nodes,
    )


# ======================================================================
# TRANSACTION INTELLIGENCE
# ======================================================================

def build_transaction_intelligence(
    transactions: pd.DataFrame,
    users: pd.DataFrame,
    merchants: pd.DataFrame,
    graph_edges: pd.DataFrame,
):

    print(
        "\nBuilding unified transaction intelligence..."
    )

    tx = transactions.copy()

    # --------------------------------------------------------------
    # Normalize IDs
    # --------------------------------------------------------------

    tx["user_id"] = normalize_id(
        tx["user_id"]
    )

    tx["merchant_id"] = normalize_id(
        tx["merchant_id"],
        remove_hyphen=True,
    )

    # --------------------------------------------------------------
    # Rule-based risk
    # --------------------------------------------------------------

    tx["transaction_risk"] = numeric(
        tx,
        "transaction_risk_score",
    )

    # --------------------------------------------------------------
    # ML anomaly
    # --------------------------------------------------------------

    tx["ml_anomaly_percentile"] = numeric(
        tx,
        "ml_anomaly_percentile",
    )

    tx["ml_anomaly_flag"] = numeric(
        tx,
        "ml_anomaly_flag",
    )

    # --------------------------------------------------------------
    # User risk lookup
    #
    # IMPORTANT:
    # Stage 05/07 stores the entity risk band as "risk_band".
    # We rename it to "user_risk_band" AFTER selecting it.
    # --------------------------------------------------------------

    user_lookup = users.copy()

    user_lookup["user_id"] = normalize_id(
        user_lookup["user_id"]
    )

    user_lookup = ensure_column(
        user_lookup,
        "user_risk_score",
        0,
    )

    user_lookup = ensure_column(
        user_lookup,
        "risk_band",
        "LOW",
    )

    user_lookup = ensure_column(
        user_lookup,
        "ml_anomaly_flag",
        0,
    )

    user_lookup = ensure_column(
        user_lookup,
        "ml_anomaly_percentile",
        0,
    )

    user_lookup = (
        user_lookup[
            [
                "user_id",
                "user_risk_score",
                "risk_band",
                "ml_anomaly_flag",
                "ml_anomaly_percentile",
            ]
        ]
        .drop_duplicates(
            "user_id"
        )
        .rename(
            columns={
                "risk_band":
                    "user_risk_band",

                "ml_anomaly_flag":
                    "user_ml_anomaly_flag",

                "ml_anomaly_percentile":
                    "user_ml_anomaly_percentile",
            }
        )
    )

    user_lookup[
        "user_risk_score"
    ] = numeric(
        user_lookup,
        "user_risk_score",
    )

    # --------------------------------------------------------------
    # Merchant risk lookup
    #
    # IMPORTANT:
    # Stage 05/07 stores the entity risk band as "risk_band".
    # We rename it to "merchant_risk_band" AFTER selecting it.
    # --------------------------------------------------------------

    merchant_lookup = merchants.copy()

    merchant_lookup[
        "merchant_id"
    ] = normalize_id(
        merchant_lookup["merchant_id"],
        remove_hyphen=True,
    )

    merchant_lookup = ensure_column(
        merchant_lookup,
        "merchant_risk_score",
        0,
    )

    merchant_lookup = ensure_column(
        merchant_lookup,
        "risk_band",
        "LOW",
    )

    merchant_lookup = ensure_column(
        merchant_lookup,
        "ml_anomaly_flag",
        0,
    )

    merchant_lookup = ensure_column(
        merchant_lookup,
        "ml_anomaly_percentile",
        0,
    )

    merchant_lookup = (
        merchant_lookup[
            [
                "merchant_id",
                "merchant_risk_score",
                "risk_band",
                "ml_anomaly_flag",
                "ml_anomaly_percentile",
            ]
        ]
        .drop_duplicates(
            "merchant_id"
        )
        .rename(
            columns={
                "risk_band":
                    "merchant_risk_band",

                "ml_anomaly_flag":
                    "merchant_ml_anomaly_flag",

                "ml_anomaly_percentile":
                    "merchant_ml_anomaly_percentile",
            }
        )
    )

    merchant_lookup[
        "merchant_risk_score"
    ] = numeric(
        merchant_lookup,
        "merchant_risk_score",
    )

    # --------------------------------------------------------------
    # Merge entity risk
    # --------------------------------------------------------------

    tx = tx.merge(
        user_lookup,
        on="user_id",
        how="left",
    )

    tx = tx.merge(
        merchant_lookup,
        on="merchant_id",
        how="left",
    )

    # --------------------------------------------------------------
    # Network edge lookup
    # --------------------------------------------------------------

    edge_lookup = graph_edges.copy()

    edge_lookup["user_id"] = normalize_id(
        edge_lookup["user_id"]
    )

    edge_lookup["merchant_id"] = normalize_id(
        edge_lookup["merchant_id"],
        remove_hyphen=True,
    )

    edge_lookup["relationship_risk_score"] = numeric(
        edge_lookup,
        "relationship_risk_score",
    )

    edge_lookup = (
        edge_lookup[
            [
                "user_id",
                "merchant_id",
                "relationship_risk_score",
            ]
        ]
        .drop_duplicates(
            [
                "user_id",
                "merchant_id",
            ]
        )
    )

    edge_lookup = edge_lookup.rename(
        columns={
            "relationship_risk_score":
                "network_relationship_risk",
        }
    )

    tx = tx.merge(
        edge_lookup,
        on=[
            "user_id",
            "merchant_id",
        ],
        how="left",
    )

    # --------------------------------------------------------------
    # Fill missing signals
    # --------------------------------------------------------------

    for col in [
        "user_risk_score",
        "merchant_risk_score",
        "network_relationship_risk",
        "user_ml_anomaly_percentile",
        "merchant_ml_anomaly_percentile",
    ]:

        tx[col] = numeric(
            tx,
            col,
        )

    for col in [
        "user_ml_anomaly_flag",
        "merchant_ml_anomaly_flag",
    ]:

        tx[col] = numeric(
            tx,
            col,
        )

    # --------------------------------------------------------------
    # Unified score
    # --------------------------------------------------------------

    tx["unified_risk_score"] = (
        tx["transaction_risk"] * 0.40
        + tx["user_risk_score"] * 0.20
        + tx["merchant_risk_score"] * 0.15
        + tx["ml_anomaly_percentile"] * 0.15
        + tx["network_relationship_risk"] * 0.10
    ).clip(
        0,
        100,
    ).round(2)

    tx["unified_risk_band"] = risk_band(
        tx["unified_risk_score"]
    )

    # --------------------------------------------------------------
    # Investigation reasons
    # --------------------------------------------------------------

    tx = ensure_column(
        tx,
        "chargeback_flag",
        0,
    )

    tx = ensure_column(
        tx,
        "negative_amount_flag",
        0,
    )

    tx = ensure_column(
        tx,
        "missing_utr_flag",
        0,
    )

    reasons = []

    for row in tx.itertuples(
        index=False
    ):

        row_reasons = []

        if row.transaction_risk >= 60:
            row_reasons.append(
                "HIGH_TRANSACTION_RISK"
            )

        if row.user_risk_score >= 60:
            row_reasons.append(
                "HIGH_USER_RISK"
            )

        if row.merchant_risk_score >= 60:
            row_reasons.append(
                "HIGH_MERCHANT_RISK"
            )

        if row.ml_anomaly_percentile >= 95:
            row_reasons.append(
                "ML_ANOMALY"
            )

        if row.network_relationship_risk >= 60:
            row_reasons.append(
                "HIGH_NETWORK_RISK"
            )

        if getattr(
            row,
            "chargeback_flag",
            0,
        ):
            row_reasons.append(
                "CHARGEBACK"
            )

        if getattr(
            row,
            "negative_amount_flag",
            0,
        ):
            row_reasons.append(
                "NEGATIVE_AMOUNT"
            )

        if getattr(
            row,
            "missing_utr_flag",
            0,
        ):
            row_reasons.append(
                "MISSING_UTR"
            )

        if not row_reasons:
            row_reasons.append(
                "NO_MAJOR_SIGNAL"
            )

        reasons.append(
            "|".join(row_reasons)
        )

    tx["investigation_reasons"] = reasons

    print(
        f"✓ Transaction intelligence: "
        f"{len(tx):,}"
    )

    return tx


# ======================================================================
# USER INTELLIGENCE
# ======================================================================

def build_user_intelligence(
    users: pd.DataFrame,
    user_network: pd.DataFrame,
    user_nodes: pd.DataFrame,
):

    print(
        "\nBuilding unified user intelligence..."
    )

    df = users.copy()

    df["user_id"] = normalize_id(
        df["user_id"]
    )

    # --------------------------------------------------------------
    # Make sure required risk columns exist
    # --------------------------------------------------------------

    df = ensure_column(
        df,
        "user_risk_score",
        0,
    )

    df = ensure_column(
        df,
        "ml_anomaly_percentile",
        0,
    )

    # --------------------------------------------------------------
    # Merge network data
    # --------------------------------------------------------------

    network = user_network.copy()

    network["user_id"] = normalize_id(
        network["user_id"]
    )

    df = df.merge(
        network,
        on="user_id",
        how="left",
    )

    # --------------------------------------------------------------
    # Merge graph node data
    # --------------------------------------------------------------

    nodes = user_nodes.copy()

    if not nodes.empty:

        nodes = nodes.rename(
            columns={
                "entity_id": "user_id",
            }
        )

        nodes["user_id"] = normalize_id(
            nodes["user_id"]
        )

        node_cols = [
            "user_id",
            "degree",
            "component_id",
            "network_activity_score",
            "suspicious_component_flag",
        ]

        node_cols = [
            col
            for col in node_cols
            if col in nodes.columns
        ]

        df = df.merge(
            nodes[node_cols],
            on="user_id",
            how="left",
        )

    # --------------------------------------------------------------
    # Numeric defaults
    # --------------------------------------------------------------

    for col in [
        "user_risk_score",
        "ml_anomaly_percentile",
        "network_merchant_count",
        "network_transaction_count",
        "network_total_amount",
        "network_chargeback_count",
        "network_chargeback_rate",
        "avg_relationship_risk",
        "max_relationship_risk",
        "degree",
        "network_activity_score",
        "suspicious_component_flag",
    ]:

        df[col] = numeric(
            df,
            col,
        )

    # --------------------------------------------------------------
    # Unified user score
    # --------------------------------------------------------------

    df["unified_user_risk_score"] = (
        df["user_risk_score"] * 0.55
        + df["ml_anomaly_percentile"] * 0.20
        + df["network_activity_score"] * 0.10
        + df["avg_relationship_risk"] * 0.10
        + df["suspicious_component_flag"] * 5
    ).clip(
        0,
        100,
    ).round(2)

    df["unified_user_risk_band"] = risk_band(
        df[
            "unified_user_risk_score"
        ]
    )

    # --------------------------------------------------------------
    # Reasons
    # --------------------------------------------------------------

    reasons = []

    for row in df.itertuples(
        index=False
    ):

        row_reasons = []

        if row.user_risk_score >= 60:
            row_reasons.append(
                "HIGH_BEHAVIORAL_RISK"
            )

        if row.ml_anomaly_percentile >= 95:
            row_reasons.append(
                "ML_ANOMALY"
            )

        if row.network_merchant_count >= 5:
            row_reasons.append(
                "MULTIPLE_MERCHANT_CONNECTIONS"
            )

        if row.network_chargeback_rate >= 0.10:
            row_reasons.append(
                "HIGH_NETWORK_CHARGEBACK_RATE"
            )

        if row.suspicious_component_flag == 1:
            row_reasons.append(
                "SUSPICIOUS_NETWORK_COMPONENT"
            )

        if not row_reasons:
            row_reasons.append(
                "NO_MAJOR_SIGNAL"
            )

        reasons.append(
            "|".join(row_reasons)
        )

    df["investigation_reasons"] = reasons

    print(
        f"✓ User intelligence: "
        f"{len(df):,}"
    )

    return df


# ======================================================================
# MERCHANT INTELLIGENCE
# ======================================================================

def build_merchant_intelligence(
    merchants: pd.DataFrame,
    merchant_network: pd.DataFrame,
    merchant_nodes: pd.DataFrame,
):

    print(
        "\nBuilding unified merchant intelligence..."
    )

    df = merchants.copy()

    df["merchant_id"] = normalize_id(
        df["merchant_id"],
        remove_hyphen=True,
    )

    # --------------------------------------------------------------
    # Required risk columns
    # --------------------------------------------------------------

    df = ensure_column(
        df,
        "merchant_risk_score",
        0,
    )

    df = ensure_column(
        df,
        "ml_anomaly_percentile",
        0,
    )

    # --------------------------------------------------------------
    # Network data
    # --------------------------------------------------------------

    network = merchant_network.copy()

    network["merchant_id"] = normalize_id(
        network["merchant_id"],
        remove_hyphen=True,
    )

    df = df.merge(
        network,
        on="merchant_id",
        how="left",
    )

    # --------------------------------------------------------------
    # Graph node data
    # --------------------------------------------------------------

    nodes = merchant_nodes.copy()

    if not nodes.empty:

        nodes = nodes.rename(
            columns={
                "entity_id": "merchant_id",
            }
        )

        nodes["merchant_id"] = normalize_id(
            nodes["merchant_id"],
            remove_hyphen=True,
        )

        node_cols = [
            "merchant_id",
            "degree",
            "component_id",
            "network_activity_score",
            "suspicious_component_flag",
        ]

        node_cols = [
            col
            for col in node_cols
            if col in nodes.columns
        ]

        df = df.merge(
            nodes[node_cols],
            on="merchant_id",
            how="left",
        )

    # --------------------------------------------------------------
    # Numeric defaults
    # --------------------------------------------------------------

    for col in [
        "merchant_risk_score",
        "ml_anomaly_percentile",
        "network_user_count",
        "network_transaction_count",
        "network_total_amount",
        "network_chargeback_count",
        "network_chargeback_rate",
        "avg_relationship_risk",
        "max_relationship_risk",
        "degree",
        "network_activity_score",
        "suspicious_component_flag",
    ]:

        df[col] = numeric(
            df,
            col,
        )

    # --------------------------------------------------------------
    # Unified merchant score
    # --------------------------------------------------------------

    df["unified_merchant_risk_score"] = (
        df["merchant_risk_score"] * 0.55
        + df["ml_anomaly_percentile"] * 0.20
        + df["network_activity_score"] * 0.10
        + df["avg_relationship_risk"] * 0.10
        + df["suspicious_component_flag"] * 5
    ).clip(
        0,
        100,
    ).round(2)

    df["unified_merchant_risk_band"] = risk_band(
        df[
            "unified_merchant_risk_score"
        ]
    )

    # --------------------------------------------------------------
    # Reasons
    # --------------------------------------------------------------

    reasons = []

    for row in df.itertuples(
        index=False
    ):

        row_reasons = []

        if row.merchant_risk_score >= 60:
            row_reasons.append(
                "HIGH_MERCHANT_RISK"
            )

        if row.ml_anomaly_percentile >= 95:
            row_reasons.append(
                "ML_ANOMALY"
            )

        if row.network_user_count >= 5:
            row_reasons.append(
                "MANY_CONNECTED_USERS"
            )

        if row.network_chargeback_rate >= 0.10:
            row_reasons.append(
                "HIGH_NETWORK_CHARGEBACK_RATE"
            )

        if row.suspicious_component_flag == 1:
            row_reasons.append(
                "SUSPICIOUS_NETWORK_COMPONENT"
            )

        if not row_reasons:
            row_reasons.append(
                "NO_MAJOR_SIGNAL"
            )

        reasons.append(
            "|".join(row_reasons)
        )

    df["investigation_reasons"] = reasons

    print(
        f"✓ Merchant intelligence: "
        f"{len(df):,}"
    )

    return df


# ======================================================================
# INVESTIGATION QUEUE
# ======================================================================

def build_investigation_queue(
    transaction_intelligence: pd.DataFrame,
    user_intelligence: pd.DataFrame,
    merchant_intelligence: pd.DataFrame,
):

    print(
        "\nBuilding investigator queue..."
    )

    # --------------------------------------------------------------
    # Transaction queue
    # --------------------------------------------------------------

    tx = transaction_intelligence.copy()

    tx["investigation_priority"] = (
        tx["unified_risk_score"]
    )

    tx_queue = tx[
        tx["unified_risk_score"] >= 50
    ].copy()

    tx_queue["entity_type"] = (
        "TRANSACTION"
    )

    tx_queue["entity_id"] = string(
        tx_queue,
        "txn_id",
    )

    tx_queue["risk_score"] = (
        tx_queue[
            "unified_risk_score"
        ]
    )

    tx_queue["risk_band"] = (
        tx_queue[
            "unified_risk_band"
        ]
    )

    tx_queue["reasons"] = (
        tx_queue[
            "investigation_reasons"
        ]
    )

    # --------------------------------------------------------------
    # User queue
    # --------------------------------------------------------------

    users = user_intelligence.copy()

    user_queue = users[
        users[
            "unified_user_risk_score"
        ] >= 50
    ].copy()

    user_queue["entity_type"] = (
        "USER"
    )

    user_queue["entity_id"] = string(
        user_queue,
        "user_id",
    )

    user_queue["risk_score"] = (
        user_queue[
            "unified_user_risk_score"
        ]
    )

    user_queue["risk_band"] = (
        user_queue[
            "unified_user_risk_band"
        ]
    )

    user_queue["reasons"] = (
        user_queue[
            "investigation_reasons"
        ]
    )

    # --------------------------------------------------------------
    # Merchant queue
    # --------------------------------------------------------------

    merchants = merchant_intelligence.copy()

    merchant_queue = merchants[
        merchants[
            "unified_merchant_risk_score"
        ] >= 50
    ].copy()

    merchant_queue["entity_type"] = (
        "MERCHANT"
    )

    merchant_queue["entity_id"] = string(
        merchant_queue,
        "merchant_id",
    )

    merchant_queue["risk_score"] = (
        merchant_queue[
            "unified_merchant_risk_score"
        ]
    )

    merchant_queue["risk_band"] = (
        merchant_queue[
            "unified_merchant_risk_band"
        ]
    )

    merchant_queue["reasons"] = (
        merchant_queue[
            "investigation_reasons"
        ]
    )

    # --------------------------------------------------------------
    # Common output
    # --------------------------------------------------------------

    columns = [
        "entity_type",
        "entity_id",
        "risk_score",
        "risk_band",
        "reasons",
    ]

    queue_parts = []

    for frame in [
        tx_queue,
        user_queue,
        merchant_queue,
    ]:

        if not frame.empty:
            queue_parts.append(
                frame[columns]
            )

    if queue_parts:

        queue = pd.concat(
            queue_parts,
            ignore_index=True,
        )

    else:

        queue = pd.DataFrame(
            columns=columns
        )

    if not queue.empty:

        queue = queue.sort_values(
            "risk_score",
            ascending=False,
        ).reset_index(
            drop=True
        )

        queue.insert(
            0,
            "priority_rank",
            range(
                1,
                len(queue) + 1,
            ),
        )

    print(
        f"✓ Investigation queue: "
        f"{len(queue):,}"
    )

    return queue


# ======================================================================
# REPORT
# ======================================================================

def build_report(
    transaction_intelligence,
    user_intelligence,
    merchant_intelligence,
    investigation_queue,
    suspicious_networks,
):

    tx_band = (
        transaction_intelligence[
            "unified_risk_band"
        ]
        .value_counts()
        .to_dict()
    )

    user_band = (
        user_intelligence[
            "unified_user_risk_band"
        ]
        .value_counts()
        .to_dict()
    )

    merchant_band = (
        merchant_intelligence[
            "unified_merchant_risk_band"
        ]
        .value_counts()
        .to_dict()
    )

    report = {

        "pipeline": {
            "stage": 8,
            "name": "Unified Fraud Intelligence",
        },

        "rows": {
            "transactions": int(
                len(transaction_intelligence)
            ),
            "users": int(
                len(user_intelligence)
            ),
            "merchants": int(
                len(merchant_intelligence)
            ),
            "investigation_queue": int(
                len(investigation_queue)
            ),
            "suspicious_networks": int(
                len(suspicious_networks)
            ),
        },

        "risk_distribution": {
            "transactions": tx_band,
            "users": user_band,
            "merchants": merchant_band,
        },

        "scoring": {
            "transaction_weight": 0.40,
            "user_weight": 0.20,
            "merchant_weight": 0.15,
            "ml_anomaly_weight": 0.15,
            "network_weight": 0.10,
        },

        "investigation_queue": {
            "high_priority_entities": int(
                (
                    investigation_queue[
                        "risk_score"
                    ] > 75
                ).sum()
                if not investigation_queue.empty
                else 0
            ),

            "medium_high_priority_entities": int(
                (
                    investigation_queue[
                        "risk_score"
                    ] > 50
                ).sum()
                if not investigation_queue.empty
                else 0
            ),
        },

        "notes": [
            (
                "Unified scores combine deterministic "
                "risk, entity risk, ML anomaly, and "
                "network relationship signals."
            ),

            (
                "Scores are investigation indicators "
                "and are not calibrated probabilities."
            ),

            (
                "Suspicious network candidates indicate "
                "patterns requiring investigation, not "
                "confirmed fraud."
            ),
        ],
    }

    return report


# ======================================================================
# MAIN
# ======================================================================

def main():

    print("=" * 70)

    print(
        "UPI SENTINEL — UNIFIED FRAUD INTELLIGENCE"
    )

    print("=" * 70)

    # --------------------------------------------------------------
    # Load
    # --------------------------------------------------------------

    (
        transactions,
        users,
        merchants,
        graph_edges,
        graph_nodes,
        suspicious_networks,
    ) = load_data()

    # --------------------------------------------------------------
    # Network intelligence
    # --------------------------------------------------------------

    (
        user_network,
        merchant_network,
        user_nodes,
        merchant_nodes,
    ) = build_network_lookup(
        graph_edges,
        graph_nodes,
        suspicious_networks,
    )

    # --------------------------------------------------------------
    # Transaction intelligence
    # --------------------------------------------------------------

    transaction_intelligence = (
        build_transaction_intelligence(
            transactions,
            users,
            merchants,
            graph_edges,
        )
    )

    # --------------------------------------------------------------
    # User intelligence
    # --------------------------------------------------------------

    user_intelligence = (
        build_user_intelligence(
            users,
            user_network,
            user_nodes,
        )
    )

    # --------------------------------------------------------------
    # Merchant intelligence
    # --------------------------------------------------------------

    merchant_intelligence = (
        build_merchant_intelligence(
            merchants,
            merchant_network,
            merchant_nodes,
        )
    )

    # --------------------------------------------------------------
    # Investigation queue
    # --------------------------------------------------------------

    investigation_queue = (
        build_investigation_queue(
            transaction_intelligence,
            user_intelligence,
            merchant_intelligence,
        )
    )

    # --------------------------------------------------------------
    # Save
    # --------------------------------------------------------------

    print(
        "\nSaving unified intelligence..."
    )

    transaction_intelligence.to_csv(
        TRANSACTION_OUTPUT,
        index=False,
    )

    user_intelligence.to_csv(
        USER_OUTPUT,
        index=False,
    )

    merchant_intelligence.to_csv(
        MERCHANT_OUTPUT,
        index=False,
    )

    investigation_queue.to_csv(
        INVESTIGATION_QUEUE_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------------
    # Report
    # --------------------------------------------------------------

    report = build_report(
        transaction_intelligence,
        user_intelligence,
        merchant_intelligence,
        investigation_queue,
        suspicious_networks,
    )

    with open(
        REPORT_OUTPUT,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            report,
            f,
            indent=2,
            default=str,
        )

    # --------------------------------------------------------------
    # Final output
    # --------------------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "UNIFIED FRAUD INTELLIGENCE COMPLETE"
    )

    print("=" * 70)

    print(
        f"Transaction intelligence: "
        f"{len(transaction_intelligence):,}"
    )

    print(
        f"User intelligence: "
        f"{len(user_intelligence):,}"
    )

    print(
        f"Merchant intelligence: "
        f"{len(merchant_intelligence):,}"
    )

    print(
        f"Investigation queue: "
        f"{len(investigation_queue):,}"
    )

    if not investigation_queue.empty:

        print(
            "\nTop investigation candidates:"
        )

        print(
            investigation_queue[
                [
                    "priority_rank",
                    "entity_type",
                    "entity_id",
                    "risk_score",
                    "risk_band",
                    "reasons",
                ]
            ]
            .head(10)
            .to_string(
                index=False
            )
        )

    print("\nSaved:")

    print(
        f"✓ {TRANSACTION_OUTPUT}"
    )

    print(
        f"✓ {USER_OUTPUT}"
    )

    print(
        f"✓ {MERCHANT_OUTPUT}"
    )

    print(
        f"✓ {INVESTIGATION_QUEUE_OUTPUT}"
    )

    print(
        f"✓ {REPORT_OUTPUT}"
    )


if __name__ == "__main__":
    main()
