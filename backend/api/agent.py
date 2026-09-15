from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.llm import interpret_query, explain_result


router = APIRouter()

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


# ============================================================
# REQUEST MODEL
# ============================================================

class AgentQuery(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


# ============================================================
# DATA LOADING
# ============================================================

def load_file(name: str) -> pd.DataFrame:
    path = DATA_DIR / name

    if not path.exists():
        raise FileNotFoundError(name)

    return pd.read_csv(path)


@lru_cache(maxsize=1)
def transactions() -> pd.DataFrame:
    df = load_file("transaction_intelligence.csv")

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

    return df


@lru_cache(maxsize=1)
def users() -> pd.DataFrame:
    return load_file("user_intelligence.csv")


@lru_cache(maxsize=1)
def networks() -> pd.DataFrame:
    return load_file("suspicious_networks.csv")


@lru_cache(maxsize=1)
def queue() -> pd.DataFrame:
    return load_file("investigation_queue.csv")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def numeric_series(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:
    return pd.to_numeric(
        df[column],
        errors="coerce",
    )


def find_first_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    for column in candidates:
        if column in df.columns:
            return column

    return None


# ============================================================
# MERCHANT CATEGORY ANALYSIS
# ============================================================

def merchant_analysis() -> Dict[str, Any]:

    df = transactions().copy()

    required_columns = [
        "merchant_category",
        "txn_id",
        "chargeback_flag",
        "timestamp",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing transaction columns: {missing}"
        )

    df = df[
        df["merchant_category"].notna()
    ].copy()

    # --------------------------------------------------------
    # Latest available quarter
    # --------------------------------------------------------

    latest = df["timestamp"].max()

    if pd.notna(latest):

        period = latest.to_period("Q")

        df = df[
            df["timestamp"].dt.to_period("Q")
            == period
        ]

        period_name = str(period)

    else:
        period_name = "All available data"

    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    result = (
        df.groupby("merchant_category")
        .agg(
            transactions=("txn_id", "nunique"),
            chargebacks=("chargeback_flag", "sum"),
        )
        .reset_index()
    )

    result["ratio"] = (
        result["chargebacks"]
        / result["transactions"].replace(0, pd.NA)
        * 100
    )

    result = result.dropna(
        subset=["ratio"]
    )

    result = result.sort_values(
        ["ratio", "transactions"],
        ascending=[False, False],
    ).head(10)

    rows = []

    for _, r in result.iterrows():

        rows.append(
            {
                "label": str(
                    r["merchant_category"]
                ),
                "value": round(
                    float(r["ratio"]),
                    2,
                ),
                "transactions": int(
                    r["transactions"]
                ),
                "chargebacks": int(
                    r["chargebacks"]
                ),
            }
        )

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "percent",
        "period": period_name,
        "metric": "chargeback_to_transaction_ratio",
    }


# ============================================================
# USER RISK ANALYSIS
# ============================================================

def user_analysis() -> Dict[str, Any]:

    df = users().copy()

    required_columns = [
        "user_id",
        "unified_user_risk_score",
        "unified_user_risk_band",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing user columns: {missing}"
        )

    df["unified_user_risk_score"] = pd.to_numeric(
        df["unified_user_risk_score"],
        errors="coerce",
    )

    result = (
        df.dropna(
            subset=[
                "unified_user_risk_score"
            ]
        )
        .sort_values(
            "unified_user_risk_score",
            ascending=False,
        )
        .head(10)
    )

    rows = []

    for _, r in result.iterrows():

        rows.append(
            {
                "label": str(
                    r["user_id"]
                ),
                "value": round(
                    float(
                        r[
                            "unified_user_risk_score"
                        ]
                    ),
                    2,
                ),
                "risk_band": str(
                    r[
                        "unified_user_risk_band"
                    ]
                ),
            }
        )

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "risk score",
        "metric": "unified_user_risk_score",
    }


# ============================================================
# SUSPICIOUS NETWORK ANALYSIS
# ============================================================

def network_analysis() -> Dict[str, Any]:

    df = networks().copy()

    required_columns = [
        "component_id",
        "network_risk_score",
        "chargeback_rate",
        "risk_band",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing network columns: {missing}"
        )

    df["network_risk_score"] = pd.to_numeric(
        df["network_risk_score"],
        errors="coerce",
    )

    df["chargeback_rate"] = pd.to_numeric(
        df["chargeback_rate"],
        errors="coerce",
    )

    transaction_count_column = find_first_column(
        df,
        [
            "transaction_count",
            "transactions",
            "txn_count",
            "edge_count",
            "transaction_cnt",
        ],
    )

    result = (
        df.dropna(
            subset=[
                "network_risk_score"
            ]
        )
        .sort_values(
            [
                "network_risk_score",
                "chargeback_rate",
            ],
            ascending=False,
        )
        .head(10)
    )

    rows = []

    for _, r in result.iterrows():

        row = {
            "label": (
                f"Network "
                f"{r['component_id']}"
            ),

            "value": round(
                float(
                    r["network_risk_score"]
                ),
                2,
            ),

            "risk_score": round(
                float(
                    r["network_risk_score"]
                ),
                2,
            ),

            "chargeback_rate": round(
                float(
                    r["chargeback_rate"]
                ),
                2,
            ),

            "risk_band": str(
                r["risk_band"]
            ),
        }

        if transaction_count_column:

            transaction_value = pd.to_numeric(
                r[transaction_count_column],
                errors="coerce",
            )

            row["transactions"] = (
                int(transaction_value)
                if pd.notna(transaction_value)
                else 0
            )

        rows.append(row)

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "risk score",
        "period": "All available data",
        "metric": "network_risk_score",
        "secondary_metric": "chargeback_rate",
    }


# ============================================================
# NETWORK CHARGEBACK RATE ANALYSIS
# ============================================================

def network_chargeback_analysis() -> Dict[str, Any]:

    df = networks().copy()

    required_columns = [
        "component_id",
        "network_risk_score",
        "chargeback_rate",
        "risk_band",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing network columns: {missing}"
        )

    df["network_risk_score"] = pd.to_numeric(
        df["network_risk_score"],
        errors="coerce",
    )

    df["chargeback_rate"] = pd.to_numeric(
        df["chargeback_rate"],
        errors="coerce",
    )

    result = (
        df.dropna(
            subset=["chargeback_rate"]
        )
        .sort_values(
            [
                "chargeback_rate",
                "network_risk_score",
            ],
            ascending=False,
        )
        .head(10)
    )

    rows = []

    for _, r in result.iterrows():

        rows.append(
            {
                "label": (
                    f"Network "
                    f"{r['component_id']}"
                ),

                "value": round(
                    float(
                        r["chargeback_rate"]
                    ),
                    2,
                ),

                "chargeback_rate": round(
                    float(
                        r["chargeback_rate"]
                    ),
                    2,
                ),

                "network_risk_score": round(
                    float(
                        r["network_risk_score"]
                    ),
                    2,
                ),

                "risk_band": str(
                    r["risk_band"]
                ),
            }
        )

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "percent chargeback rate",
        "period": "All available data",
        "metric": "network_chargeback_rate",
        "secondary_metric": "network_risk_score",
    }


# ============================================================
# INVESTIGATION QUEUE ANALYSIS
# ============================================================

def queue_analysis() -> Dict[str, Any]:

    df = queue().copy()

    required_columns = [
        "entity_type",
        "entity_id",
        "risk_score",
        "risk_band",
        "priority_rank",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing investigation columns: {missing}"
        )

    df["risk_score"] = pd.to_numeric(
        df["risk_score"],
        errors="coerce",
    )

    df["priority_rank"] = pd.to_numeric(
        df["priority_rank"],
        errors="coerce",
    )

    result = (
        df.dropna(
            subset=["risk_score"]
        )
        .sort_values(
            "priority_rank",
            ascending=True,
        )
        .head(10)
    )

    rows = []

    for _, r in result.iterrows():

        rows.append(
            {
                "label": (
                    f"{r['entity_type']} "
                    f"{r['entity_id']}"
                ),

                "value": round(
                    float(
                        r["risk_score"]
                    ),
                    2,
                ),

                "risk_band": str(
                    r["risk_band"]
                ),

                "priority_rank": int(
                    r["priority_rank"]
                ),
            }
        )

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "risk score",
        "metric": "investigation_risk_score",
    }


# ============================================================
# RISK DISTRIBUTION
# ============================================================

def risk_distribution_analysis() -> Dict[str, Any]:

    df = users().copy()

    band_column = find_first_column(
        df,
        [
            "unified_user_risk_band",
            "risk_band",
            "user_risk_band",
        ],
    )

    if not band_column:
        raise ValueError(
            "No risk band column found in user intelligence."
        )

    counts = (
        df[band_column]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
        .value_counts()
    )

    preferred_order = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        "UNKNOWN",
    ]

    rows = []

    for band in preferred_order:

        if band not in counts.index:
            continue

        rows.append(
            {
                "label": band,
                "value": int(
                    counts[band]
                ),
            }
        )

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "users",
        "metric": "user_risk_distribution",
    }


# ============================================================
# TRANSACTION STATUS DISTRIBUTION
# ============================================================

def transaction_status_analysis() -> Dict[str, Any]:

    df = transactions().copy()

    status_column = find_first_column(
        df,
        [
            "status",
            "transaction_status",
            "txn_status",
        ],
    )

    if not status_column:
        raise ValueError(
            "No transaction status column found."
        )

    counts = (
        df[status_column]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
        .value_counts()
    )

    rows = []

    for label, value in counts.items():

        rows.append(
            {
                "label": str(label),
                "value": int(value),
            }
        )

    rows = rows[:10]

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "transactions",
        "metric": "transaction_status_distribution",
    }


# ============================================================
# TRANSACTION ACTIVITY TREND
# ============================================================

def transaction_trend_analysis() -> Dict[str, Any]:

    df = transactions().copy()

    required_columns = [
        "txn_id",
        "timestamp",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing transaction columns: {missing}"
        )

    df = df.dropna(
        subset=["timestamp"]
    ).copy()

    if df.empty:
        return {
            "rows": [],
            "labels": [],
            "values": [],
            "unit": "transactions",
            "metric": "monthly_transaction_count",
        }

    df["month"] = (
        df["timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    result = (
        df.groupby("month")
        .agg(
            transactions=(
                "txn_id",
                "nunique",
            )
        )
        .reset_index()
        .sort_values("month")
    )

    rows = []

    for _, r in result.iterrows():

        rows.append(
            {
                "label": str(
                    r["month"]
                ),
                "value": int(
                    r["transactions"]
                ),
            }
        )

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "transactions",
        "period": "Monthly",
        "metric": "monthly_transaction_count",
    }


# ============================================================
# CHARGEBACK TREND
# ============================================================

def chargeback_trend_analysis() -> Dict[str, Any]:

    df = transactions().copy()

    required_columns = [
        "timestamp",
        "chargeback_flag",
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing chargeback columns: {missing}"
        )

    df = df.dropna(
        subset=["timestamp"]
    ).copy()

    df["chargeback_flag"] = pd.to_numeric(
        df["chargeback_flag"],
        errors="coerce",
    ).fillna(0)

    if df.empty:
        return {
            "rows": [],
            "labels": [],
            "values": [],
            "unit": "chargebacks",
            "metric": "monthly_chargeback_count",
        }

    df["month"] = (
        df["timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    result = (
        df.groupby("month")
        .agg(
            chargebacks=(
                "chargeback_flag",
                "sum",
            )
        )
        .reset_index()
        .sort_values("month")
    )

    rows = []

    for _, r in result.iterrows():

        rows.append(
            {
                "label": str(
                    r["month"]
                ),
                "value": int(
                    r["chargebacks"]
                ),
            }
        )

    return {
        "rows": rows,
        "labels": [
            r["label"]
            for r in rows
        ],
        "values": [
            r["value"]
            for r in rows
        ],
        "unit": "chargebacks",
        "period": "Monthly",
        "metric": "monthly_chargeback_count",
    }


# ============================================================
# FALLBACK AI ROUTING
# ============================================================

def fallback(question: str) -> Dict[str, Any]:

    q = question.lower()

    # --------------------------------------------------------
    # Transaction trend
    # --------------------------------------------------------

    if (
        "trend" in q
        or "over time" in q
        or "monthly transaction" in q
        or "transaction activity" in q
        or "transactions over" in q
    ):

        return {
            "intent": "transaction_trend",
            "chart_type": "line",
            "title": "Transaction Activity Over Time",
            "time_scope": "all_data",
        }

    # --------------------------------------------------------
    # Chargeback trend
    # --------------------------------------------------------

    if (
        "chargeback trend" in q
        or "chargebacks over time" in q
        or "chargebacks by month" in q
        or "monthly chargebacks" in q
    ):

        return {
            "intent": "chargeback_trend",
            "chart_type": "line",
            "title": "Chargeback Trend",
            "time_scope": "all_data",
        }

    # --------------------------------------------------------
    # Risk distribution
    # --------------------------------------------------------

    if (
        "risk distribution" in q
        or "risk breakdown" in q
        or "distribution of risk" in q
        or "how many low" in q
        or "how many high" in q
    ):

        return {
            "intent": "risk_distribution",
            "chart_type": "donut",
            "title": "User Risk Distribution",
            "time_scope": "all_data",
        }

    # --------------------------------------------------------
    # Transaction status
    # --------------------------------------------------------

    if (
        "failed vs successful" in q
        or "successful vs failed" in q
        or "transaction status" in q
        or "status distribution" in q
        or "failed transactions" in q
    ):

        return {
            "intent": "transaction_status",
            "chart_type": "donut",
            "title": "Transaction Status Distribution",
            "time_scope": "all_data",
        }

    # --------------------------------------------------------
    # Merchant questions
    # --------------------------------------------------------

    if (
        "merchant" in q
        or "category" in q
        or "chargeback ratio" in q
        or "chargeback rate" in q
    ):

        return {
            "intent": "merchant_chargeback_ratio",
            "chart_type": "bar",
            "title": (
                "Chargeback-to-Transaction Ratio "
                "by Merchant Category"
            ),
            "time_scope": "latest_quarter",
        }

    # --------------------------------------------------------
    # Network chargeback question
    # --------------------------------------------------------

    if (
        "network" in q
        and (
            "chargeback" in q
            or "dispute" in q
        )
    ):

        return {
            "intent": "network_chargeback_rate",
            "chart_type": "bar",
            "title": (
                "Top Networks by Chargeback Rate"
            ),
            "time_scope": "all_data",
        }

    # --------------------------------------------------------
    # Network risk
    # --------------------------------------------------------

    if (
        "network" in q
        or "ring" in q
        or "connected" in q
        or "suspicious network" in q
    ):

        return {
            "intent": "suspicious_networks",
            "chart_type": "bar",
            "title": (
                "Top Suspicious Networks "
                "by Risk Score"
            ),
            "time_scope": "all_data",
        }

    # --------------------------------------------------------
    # User questions
    # --------------------------------------------------------

    if (
        "user" in q
        or "customer" in q
        or "account" in q
    ):

        return {
            "intent": "highest_risk_users",
            "chart_type": "bar",
            "title": "Highest-Risk Users",
            "time_scope": "all_data",
        }

    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    return {
        "intent": "investigation_queue",
        "chart_type": "bar",
        "title": "Investigation Priority Queue",
        "time_scope": "all_data",
    }


# ============================================================
# QUESTION REFINEMENT
#
# Groq handles natural-language understanding.
# These deterministic rules handle visualization-specific
# intent when the existing LLM router returns a broad intent.
# ============================================================

def refine_intent(
    question: str,
    routing: Dict[str, Any],
) -> Dict[str, Any]:

    q = question.lower().strip()

    # --------------------------------------------------------
    # Time-series questions
    # --------------------------------------------------------

    if (
        (
            "transaction" in q
            or "payment" in q
        )
        and (
            "trend" in q
            or "over time" in q
            or "by month" in q
            or "monthly" in q
        )
    ):

        return {
            "intent": "transaction_trend",
            "chart_type": "line",
            "title": "Transaction Activity Over Time",
        }

    if (
        "chargeback" in q
        and (
            "trend" in q
            or "over time" in q
            or "by month" in q
            or "monthly" in q
        )
    ):

        return {
            "intent": "chargeback_trend",
            "chart_type": "line",
            "title": "Chargeback Trend",
        }

    # --------------------------------------------------------
    # Distribution questions
    # --------------------------------------------------------

    if (
        "risk distribution" in q
        or "risk breakdown" in q
        or "distribution of risk" in q
    ):

        return {
            "intent": "risk_distribution",
            "chart_type": "donut",
            "title": "User Risk Distribution",
        }

    if (
        (
            "failed" in q
            and "successful" in q
        )
        or "transaction status" in q
        or "status distribution" in q
    ):

        return {
            "intent": "transaction_status",
            "chart_type": "donut",
            "title": "Transaction Status Distribution",
        }

    # --------------------------------------------------------
    # Network chargeback rate
    # --------------------------------------------------------

    if (
        (
            "network" in q
            or "ring" in q
        )
        and (
            "chargeback rate" in q
            or "chargeback ratio" in q
            or "highest chargeback" in q
        )
    ):

        return {
            "intent": "network_chargeback_rate",
            "chart_type": "bar",
            "title": "Top Networks by Chargeback Rate",
        }

    # --------------------------------------------------------
    # Existing AI routing
    # --------------------------------------------------------

    return routing


# ============================================================
# CHART CONFIGURATION
# ============================================================

CHART_CONFIG = {

    "highest_risk_users": {
        "chart_type": "bar",
        "title": "Highest-Risk Users",
    },

    "merchant_chargeback_ratio": {
        "chart_type": "bar",
        "title": (
            "Chargeback-to-Transaction Ratio "
            "by Merchant Category"
        ),
    },

    "suspicious_networks": {
        "chart_type": "bar",
        "title": (
            "Top Suspicious Networks "
            "by Risk Score"
        ),
    },

    "network_chargeback_rate": {
        "chart_type": "bar",
        "title": (
            "Top Networks by Chargeback Rate"
        ),
    },

    "investigation_queue": {
        "chart_type": "bar",
        "title": "Investigation Priority Queue",
    },

    "risk_distribution": {
        "chart_type": "donut",
        "title": "User Risk Distribution",
    },

    "transaction_status": {
        "chart_type": "donut",
        "title": "Transaction Status Distribution",
    },

    "transaction_trend": {
        "chart_type": "line",
        "title": "Transaction Activity Over Time",
    },

    "chargeback_trend": {
        "chart_type": "line",
        "title": "Chargeback Trend",
    },
}


# ============================================================
# ANALYSIS DISPATCHER
# ============================================================

def run_analysis(
    intent: str,
) -> Dict[str, Any]:

    if intent == "merchant_chargeback_ratio":
        return merchant_analysis()

    if intent == "highest_risk_users":
        return user_analysis()

    if intent == "suspicious_networks":
        return network_analysis()

    if intent == "network_chargeback_rate":
        return network_chargeback_analysis()

    if intent == "investigation_queue":
        return queue_analysis()

    if intent == "risk_distribution":
        return risk_distribution_analysis()

    if intent == "transaction_status":
        return transaction_status_analysis()

    if intent == "transaction_trend":
        return transaction_trend_analysis()

    if intent == "chargeback_trend":
        return chargeback_trend_analysis()

    return queue_analysis()


# ============================================================
# MAIN SENTINEL COPILOT ENDPOINT
# ============================================================

@router.post("/query")
def query_agent(
    payload: AgentQuery,
):

    question = payload.question.strip()

    try:

        # ====================================================
        # 1. AI ROUTING
        # ====================================================

        try:

            routing = interpret_query(
                question
            )

            ai_routing = True

        except Exception:

            routing = fallback(
                question
            )

            ai_routing = False

        # ====================================================
        # 2. REFINE INTENT
        # ====================================================

        routing = refine_intent(
            question,
            routing,
        )

        intent = routing["intent"]

        # ====================================================
        # 3. SAFE VISUALIZATION CONFIG
        # ====================================================

        config = CHART_CONFIG.get(
            intent,
            {
                "chart_type": "bar",
                "title": "Investigation Analysis",
            },
        )

        chart_type = config[
            "chart_type"
        ]

        title = config[
            "title"
        ]

        # ====================================================
        # 4. RUN ANALYSIS
        # ====================================================

        analysis = run_analysis(
            intent
        )

        analysis["intent"] = intent

        # ====================================================
        # 5. AI EXPLANATION
        # ====================================================

        try:

            explanation = explain_result(
                question,
                analysis,
            )

            ai_explanation = True

        except Exception:

            explanation = (
                "Analysis completed. "
                "Review the ranked results "
                "for investigation."
            )

            ai_explanation = False

        # ====================================================
        # 6. FINAL RESPONSE
        # ====================================================

        return {

            "question": question,

            "intent": intent,

            "chart_type": chart_type,

            "title": title,

            "analysis": analysis,

            "explanation": explanation,

            "ai_routing": ai_routing,

            "ai_explanation": ai_explanation,

        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )