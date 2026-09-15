"""
UPI SENTINEL — STAGE 06
Fraud Graph & Suspicious Network Detection

Builds a bipartite User ↔ Merchant graph from transaction data,
calculates network structure and identifies suspicious ring-like
patterns requiring investigation.

IMPORTANT:
This system detects suspicious network patterns.
It does NOT establish confirmed fraud or direct circular money flow.
"""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd


# ======================================================================
# CONFIG
# ======================================================================

BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

TRANSACTION_FILE = PROCESSED_DIR / "transaction_features.csv"
USER_FILE = PROCESSED_DIR / "user_risk_features.csv"
MERCHANT_FILE = PROCESSED_DIR / "merchant_risk_features.csv"

EDGE_OUTPUT = PROCESSED_DIR / "fraud_graph_edges.csv"
NODE_OUTPUT = PROCESSED_DIR / "fraud_graph_nodes.csv"
COMPONENT_OUTPUT = PROCESSED_DIR / "fraud_graph_components.csv"
SUSPICIOUS_OUTPUT = PROCESSED_DIR / "suspicious_networks.csv"

REPORT_OUTPUT = REPORT_DIR / "fraud_graph_report.json"


# ======================================================================
# HELPERS
# ======================================================================

def minmax(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce").fillna(0)

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(0.0, index=series.index)

    return ((series - minimum) / (maximum - minimum)).clip(0, 1)


def percentile_rank(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce").fillna(0)

    if len(series) == 0:
        return pd.Series(dtype=float)

    return series.rank(pct=True).fillna(0)


# ======================================================================
# LOAD DATA
# ======================================================================

def load_data():

    print("Loading analytical datasets...")

    transactions = pd.read_csv(TRANSACTION_FILE)
    users = pd.read_csv(USER_FILE)
    merchants = pd.read_csv(MERCHANT_FILE)

    print(f"✓ Transaction features: {len(transactions):,}")
    print(f"✓ User risk features: {len(users):,}")
    print(f"✓ Merchant risk features: {len(merchants):,}")

    return transactions, users, merchants


# ======================================================================
# PREPARE TRANSACTIONS
# ======================================================================

def prepare_transactions(transactions: pd.DataFrame) -> pd.DataFrame:

    tx = transactions.copy()

    required = ["user_id", "merchant_id"]

    for col in required:
        if col not in tx.columns:
            raise ValueError(f"Required column missing: {col}")

    tx["user_id"] = (
        tx["user_id"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    tx["merchant_id"] = (
        tx["merchant_id"]
        .astype("string")
        .str.strip()
        .str.upper()
        .str.replace("-", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    tx = tx[
        tx["user_id"].notna()
        & tx["merchant_id"].notna()
        & (tx["user_id"] != "")
        & (tx["merchant_id"] != "")
        & (tx["user_id"] != "<NA>")
        & (tx["merchant_id"] != "<NA>")
    ].copy()

    print(f"✓ Graph-eligible transactions: {len(tx):,}")

    return tx


# ======================================================================
# BUILD EDGE TABLE
# ======================================================================

def build_edges(
    transactions: pd.DataFrame,
    users: pd.DataFrame,
    merchants: pd.DataFrame,
) -> pd.DataFrame:

    print("\nBuilding User ↔ Merchant relationships...")

    tx = transactions.copy()

    # --------------------------------------------------------------
    # User lookup
    # --------------------------------------------------------------

    user_cols = ["user_id"]

    for col in [
        "user_risk_score",
        "user_risk_band",
    ]:
        if col in users.columns:
            user_cols.append(col)

    user_lookup = (
        users[user_cols]
        .drop_duplicates("user_id")
        .copy()
    )

    user_lookup["user_id"] = (
        user_lookup["user_id"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------------
    # Merchant lookup
    # --------------------------------------------------------------

    merchant_cols = ["merchant_id"]

    for col in [
        "merchant_risk_score",
        "merchant_risk_band",
    ]:
        if col in merchants.columns:
            merchant_cols.append(col)

    merchant_lookup = (
        merchants[merchant_cols]
        .drop_duplicates("merchant_id")
        .copy()
    )

    merchant_lookup["merchant_id"] = (
        merchant_lookup["merchant_id"]
        .astype("string")
        .str.strip()
        .str.upper()
        .str.replace("-", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    # --------------------------------------------------------------
    # Transaction preparation
    # --------------------------------------------------------------

    tx["amount_numeric"] = pd.to_numeric(
        tx.get("amount", 0),
        errors="coerce",
    ).fillna(0)

    tx["amount_abs"] = tx["amount_numeric"].abs()

    if "chargeback_flag" in tx.columns:
        tx["chargeback_flag_graph"] = pd.to_numeric(
            tx["chargeback_flag"],
            errors="coerce",
        ).fillna(0)
    else:
        tx["chargeback_flag_graph"] = 0

    if "failed_flag" in tx.columns:
        tx["failed_flag_graph"] = pd.to_numeric(
            tx["failed_flag"],
            errors="coerce",
        ).fillna(0)
    else:
        tx["failed_flag_graph"] = (
            tx["status"]
            .astype("string")
            .eq("FAILED")
            .fillna(False)
            .astype(int)
        )

    # --------------------------------------------------------------
    # Aggregate User ↔ Merchant relationships
    # --------------------------------------------------------------

    edges = (
        tx.groupby(
            ["user_id", "merchant_id"],
            as_index=False,
        )
        .agg(
            transaction_count=("user_id", "size"),
            total_amount=("amount_abs", "sum"),
            avg_amount=("amount_abs", "mean"),
            max_amount=("amount_abs", "max"),
            chargeback_count=("chargeback_flag_graph", "sum"),
            failed_count=("failed_flag_graph", "sum"),
        )
    )

    edges["failure_rate"] = np.where(
        edges["transaction_count"] > 0,
        edges["failed_count"] / edges["transaction_count"],
        0,
    )

    edges["chargeback_rate"] = np.where(
        edges["transaction_count"] > 0,
        edges["chargeback_count"] / edges["transaction_count"],
        0,
    )

    # --------------------------------------------------------------
    # Add user risk
    # --------------------------------------------------------------

    edges = edges.merge(
        user_lookup,
        on="user_id",
        how="left",
    )

    # --------------------------------------------------------------
    # Add merchant risk
    # --------------------------------------------------------------

    edges = edges.merge(
        merchant_lookup,
        on="merchant_id",
        how="left",
    )

    for col in [
        "user_risk_score",
        "merchant_risk_score",
    ]:
        if col in edges.columns:
            edges[col] = pd.to_numeric(
                edges[col],
                errors="coerce",
            ).fillna(0)

        else:
            edges[col] = 0

    # --------------------------------------------------------------
    # Relationship risk
    # --------------------------------------------------------------

    edges["transaction_intensity"] = percentile_rank(
        edges["transaction_count"]
    )

    edges["amount_intensity"] = percentile_rank(
        edges["total_amount"]
    )

    edges["chargeback_intensity"] = minmax(
        edges["chargeback_rate"]
    )

    edges["failure_intensity"] = minmax(
        edges["failure_rate"]
    )

    edges["relationship_risk_score"] = (
        edges["transaction_intensity"] * 20
        + edges["amount_intensity"] * 15
        + edges["chargeback_intensity"] * 30
        + edges["failure_intensity"] * 15
        + minmax(edges["user_risk_score"]) * 10
        + minmax(edges["merchant_risk_score"]) * 10
    ).round(2)

    edges["relationship_risk_band"] = pd.cut(
        edges["relationship_risk_score"],
        bins=[-np.inf, 25, 50, 75, np.inf],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        ],
        right=True,
    ).astype("string")

    print(
        f"✓ Unique User ↔ Merchant edges: "
        f"{len(edges):,}"
    )

    return edges


# ======================================================================
# BUILD NETWORKX GRAPH
# ======================================================================

def build_graph(edges: pd.DataFrame):

    print("\nBuilding NetworkX fraud graph...")

    graph = nx.Graph()

    for row in edges.itertuples(index=False):

        user = f"USER::{row.user_id}"
        merchant = f"MERCHANT::{row.merchant_id}"

        graph.add_node(
            user,
            node_type="USER",
            entity_id=row.user_id,
        )

        graph.add_node(
            merchant,
            node_type="MERCHANT",
            entity_id=row.merchant_id,
        )

        graph.add_edge(
            user,
            merchant,
            transaction_count=int(row.transaction_count),
            total_amount=float(row.total_amount),
            chargeback_count=int(row.chargeback_count),
            failure_rate=float(row.failure_rate),
            relationship_risk_score=float(
                row.relationship_risk_score
            ),
        )

    print(
        f"✓ Graph nodes: "
        f"{graph.number_of_nodes():,}"
    )

    print(
        f"✓ Graph edges: "
        f"{graph.number_of_edges():,}"
    )

    return graph


# ======================================================================
# NODE FEATURES
# ======================================================================

def build_node_features(graph):

    print("\nCalculating graph node features...")

    rows = []

    for node, attrs in graph.nodes(data=True):

        degree = graph.degree(node)

        neighbors = list(
            graph.neighbors(node)
        )

        transaction_count = 0
        total_amount = 0
        chargebacks = 0
        risk_values = []

        for neighbor in neighbors:

            edge_data = graph.get_edge_data(
                node,
                neighbor,
            )

            transaction_count += edge_data.get(
                "transaction_count",
                0,
            )

            total_amount += edge_data.get(
                "total_amount",
                0,
            )

            chargebacks += edge_data.get(
                "chargeback_count",
                0,
            )

            risk_values.append(
                edge_data.get(
                    "relationship_risk_score",
                    0,
                )
            )

        rows.append(
            {
                "node_id": node,
                "entity_id": attrs["entity_id"],
                "node_type": attrs["node_type"],
                "degree": degree,
                "transaction_count": transaction_count,
                "total_amount": total_amount,
                "chargeback_count": chargebacks,
                "avg_relationship_risk": (
                    np.mean(risk_values)
                    if risk_values
                    else 0
                ),
            }
        )

    nodes = pd.DataFrame(rows)

    nodes["degree_percentile"] = percentile_rank(
        nodes["degree"]
    )

    nodes["amount_percentile"] = percentile_rank(
        nodes["total_amount"]
    )

    nodes["network_activity_score"] = (
        nodes["degree_percentile"] * 50
        + nodes["amount_percentile"] * 50
    ).round(2)

    print(
        f"✓ Node features: {len(nodes):,}"
    )

    return nodes


# ======================================================================
# CONNECTED COMPONENTS
# ======================================================================

def build_components(graph):

    print("\nDetecting connected components...")

    components = list(
        nx.connected_components(graph)
    )

    rows = []

    for component_id, component in enumerate(
        components,
        start=1,
    ):

        users_in_component = [
            node
            for node in component
            if graph.nodes[node].get("node_type")
            == "USER"
        ]

        merchants_in_component = [
            node
            for node in component
            if graph.nodes[node].get("node_type")
            == "MERCHANT"
        ]

        subgraph = graph.subgraph(
            component
        )

        edge_count = subgraph.number_of_edges()

        possible_edges = (
            len(users_in_component)
            * len(merchants_in_component)
        )

        density = (
            edge_count / possible_edges
            if possible_edges > 0
            else 0
        )

        rows.append(
            {
                "component_id": component_id,
                "node_count": len(component),
                "user_count": len(users_in_component),
                "merchant_count": len(
                    merchants_in_component
                ),
                "edge_count": edge_count,
                "density": round(
                    density,
                    6,
                ),
            }
        )

    components_df = pd.DataFrame(rows)

    print(
        f"✓ Connected components: "
        f"{len(components_df):,}"
    )

    return components_df, components


# ======================================================================
# SUSPICIOUS NETWORK DETECTION
# ======================================================================

def detect_suspicious_networks(
    graph,
    components,
    edges,
):

    print(
        "\nDetecting suspicious network patterns..."
    )

    rows = []

    for component_id, component in enumerate(
        components,
        start=1,
    ):

        component_users = [
            graph.nodes[node]["entity_id"]
            for node in component
            if graph.nodes[node].get("node_type")
            == "USER"
        ]

        component_merchants = [
            graph.nodes[node]["entity_id"]
            for node in component
            if graph.nodes[node].get("node_type")
            == "MERCHANT"
        ]

        if (
            not component_users
            or not component_merchants
        ):
            continue

        component_edges = edges[
            edges["user_id"].isin(
                component_users
            )
            & edges["merchant_id"].isin(
                component_merchants
            )
        ]

        if component_edges.empty:
            continue

        total_transactions = component_edges[
            "transaction_count"
        ].sum()

        total_amount = component_edges[
            "total_amount"
        ].sum()

        total_chargebacks = component_edges[
            "chargeback_count"
        ].sum()

        avg_relationship_risk = component_edges[
            "relationship_risk_score"
        ].mean()

        max_relationship_risk = component_edges[
            "relationship_risk_score"
        ].max()

        density = (
            len(component_edges)
            / (
                len(component_users)
                * len(component_merchants)
            )
        )

        # Shared merchant analysis
        merchant_user_counts = (
            component_edges
            .groupby("merchant_id")["user_id"]
            .nunique()
        )

        max_shared_users = (
            merchant_user_counts.max()
            if len(merchant_user_counts)
            else 0
        )

        shared_merchant_count = (
            merchant_user_counts >= 2
        ).sum()

        chargeback_rate = (
            total_chargebacks
            / total_transactions
            if total_transactions > 0
            else 0
        )

        # ----------------------------------------------------------
        # Signals
        # ----------------------------------------------------------

        shared_merchant_signal = min(
            max_shared_users / 10,
            1,
        )

        density_signal = min(
            density,
            1,
        )

        chargeback_signal = min(
            chargeback_rate / 0.20,
            1,
        )

        relationship_signal = (
            avg_relationship_risk / 100
        )

        activity_signal = min(
            np.log1p(total_transactions)
            / np.log1p(100),
            1,
        )

        network_risk_score = (
            shared_merchant_signal * 25
            + density_signal * 20
            + chargeback_signal * 25
            + relationship_signal * 20
            + activity_signal * 10
        )

        signals = []

        if max_shared_users >= 3:
            signals.append(
                "SHARED_MERCHANT"
            )

        if shared_merchant_count >= 2:
            signals.append(
                "MULTIPLE_SHARED_MERCHANTS"
            )

        if (
            density >= 0.40
            and len(component_users) >= 3
        ):
            signals.append(
                "DENSE_USER_MERCHANT_NETWORK"
            )

        if chargeback_rate >= 0.10:
            signals.append(
                "HIGH_CHARGEBACK_CONCENTRATION"
            )

        if avg_relationship_risk >= 60:
            signals.append(
                "HIGH_RELATIONSHIP_RISK"
            )

        if len(component_users) >= 5:
            signals.append(
                "LARGE_CONNECTED_CLUSTER"
            )

        if network_risk_score >= 75:
            band = "CRITICAL"

        elif network_risk_score >= 50:
            band = "HIGH"

        elif network_risk_score >= 25:
            band = "MEDIUM"

        else:
            band = "LOW"

        suspicious = (
            len(signals) >= 2
            or network_risk_score >= 50
        )

        if suspicious:

            rows.append(
                {
                    "component_id": component_id,
                    "user_count": len(
                        component_users
                    ),
                    "merchant_count": len(
                        component_merchants
                    ),
                    "edge_count": len(
                        component_edges
                    ),
                    "total_transactions": int(
                        total_transactions
                    ),
                    "total_amount": round(
                        float(total_amount),
                        2,
                    ),
                    "total_chargebacks": int(
                        total_chargebacks
                    ),
                    "chargeback_rate": round(
                        float(chargeback_rate),
                        4,
                    ),
                    "network_density": round(
                        float(density),
                        4,
                    ),
                    "max_shared_users_per_merchant": int(
                        max_shared_users
                    ),
                    "shared_merchant_count": int(
                        shared_merchant_count
                    ),
                    "avg_relationship_risk": round(
                        float(
                            avg_relationship_risk
                        ),
                        2,
                    ),
                    "max_relationship_risk": round(
                        float(
                            max_relationship_risk
                        ),
                        2,
                    ),
                    "network_risk_score": round(
                        float(
                            network_risk_score
                        ),
                        2,
                    ),
                    "risk_band": band,
                    "signals": "|".join(
                        signals
                    ),
                }
            )

    suspicious_df = pd.DataFrame(rows)

    if not suspicious_df.empty:

        suspicious_df = (
            suspicious_df
            .sort_values(
                "network_risk_score",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    print(
        f"✓ Suspicious network candidates: "
        f"{len(suspicious_df):,}"
    )

    return suspicious_df


# ======================================================================
# REPORT
# ======================================================================

def build_report(
    transactions,
    edges,
    graph,
    nodes,
    components_df,
    suspicious_df,
):

    report = {
        "graph": {
            "eligible_transactions": int(
                len(transactions)
            ),
            "unique_user_nodes": int(
                (
                    nodes["node_type"]
                    == "USER"
                ).sum()
            ),
            "unique_merchant_nodes": int(
                (
                    nodes["node_type"]
                    == "MERCHANT"
                ).sum()
            ),
            "total_nodes": int(
                graph.number_of_nodes()
            ),
            "total_edges": int(
                graph.number_of_edges()
            ),
            "connected_components": int(
                len(components_df)
            ),
        },

        "relationships": {
            "avg_transactions_per_edge": round(
                float(
                    edges[
                        "transaction_count"
                    ].mean()
                ),
                2,
            ),
            "max_transactions_per_edge": int(
                edges[
                    "transaction_count"
                ].max()
            ),
            "avg_relationship_risk": round(
                float(
                    edges[
                        "relationship_risk_score"
                    ].mean()
                ),
                2,
            ),
            "high_risk_relationships": int(
                (
                    edges[
                        "relationship_risk_score"
                    ] >= 50
                ).sum()
            ),
        },

        "network_risk": {
            "suspicious_network_candidates": int(
                len(suspicious_df)
            ),
        },

        "risk_band_distribution": {},

        "notes": [
            "Graph represents User ↔ Merchant transaction relationships.",
            "Suspicious networks are investigation candidates, not confirmed fraud.",
            "The dataset does not provide direct user-to-user payment edges.",
            "Unmatched reference entities are not automatically treated as fraudulent.",
        ],
    }

    if not suspicious_df.empty:

        report[
            "risk_band_distribution"
        ] = (
            suspicious_df["risk_band"]
            .value_counts()
            .to_dict()
        )

    return report


# ======================================================================
# MAIN
# ======================================================================

def main():

    print("=" * 70)
    print(
        "UPI SENTINEL — FRAUD GRAPH & RING DETECTION"
    )
    print("=" * 70)

    # Load
    transactions, users, merchants = load_data()

    # Prepare
    transactions = prepare_transactions(
        transactions
    )

    # Build relationships
    edges = build_edges(
        transactions,
        users,
        merchants,
    )

    # Build graph
    graph = build_graph(edges)

    # Node features
    nodes = build_node_features(graph)

    # Connected components
    components_df, components = (
        build_components(graph)
    )

    # Suspicious networks
    suspicious_df = (
        detect_suspicious_networks(
            graph,
            components,
            edges,
        )
    )

    # --------------------------------------------------------------
    # Component ID for every node
    # --------------------------------------------------------------

    component_mapping = {}

    for component_id, component in enumerate(
        components,
        start=1,
    ):

        for node in component:
            component_mapping[node] = (
                component_id
            )

    nodes["component_id"] = nodes[
        "node_id"
    ].map(component_mapping)

    # --------------------------------------------------------------
    # Save artifacts
    # --------------------------------------------------------------

    print("\nSaving graph artifacts...")

    edges.to_csv(
        EDGE_OUTPUT,
        index=False,
    )

    nodes.to_csv(
        NODE_OUTPUT,
        index=False,
    )

    components_df.to_csv(
        COMPONENT_OUTPUT,
        index=False,
    )

    suspicious_df.to_csv(
        SUSPICIOUS_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------------
    # Report
    # --------------------------------------------------------------

    report = build_report(
        transactions,
        edges,
        graph,
        nodes,
        components_df,
        suspicious_df,
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
        "FRAUD GRAPH ANALYSIS COMPLETE"
    )
    print("=" * 70)

    print(
        f"Graph nodes: "
        f"{graph.number_of_nodes():,}"
    )

    print(
        f"Graph edges: "
        f"{graph.number_of_edges():,}"
    )

    print(
        f"Connected components: "
        f"{len(components_df):,}"
    )

    print(
        f"Suspicious network candidates: "
        f"{len(suspicious_df):,}"
    )

    if not suspicious_df.empty:

        print(
            "\nTop suspicious networks:"
        )

        display_cols = [
            "component_id",
            "user_count",
            "merchant_count",
            "edge_count",
            "network_density",
            "chargeback_rate",
            "network_risk_score",
            "risk_band",
            "signals",
        ]

        print(
            suspicious_df[
                display_cols
            ]
            .head(10)
            .to_string(index=False)
        )

    print("\nSaved:")
    print(f"✓ {EDGE_OUTPUT}")
    print(f"✓ {NODE_OUTPUT}")
    print(f"✓ {COMPONENT_OUTPUT}")
    print(f"✓ {SUSPICIOUS_OUTPUT}")
    print(f"✓ {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()