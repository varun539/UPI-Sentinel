"""
UPI SENTINEL — STAGE 07
ML Anomaly Detection

Uses Isolation Forest to identify unusual:
1. Transactions
2. Users
3. Merchants

IMPORTANT:
ML anomaly scores are NOT confirmed fraud probabilities.
They are investigation signals that complement:
- behavioral risk
- KYC risk
- chargebacks
- merchant risk
- fraud-network signals
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ======================================================================
# CONFIG
# ======================================================================

BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ----------------------------------------------------------------------
# INPUTS
# ----------------------------------------------------------------------

TRANSACTION_INPUT = (
    PROCESSED_DIR
    / "transaction_features.csv"
)

USER_INPUT = (
    PROCESSED_DIR
    / "user_risk_features.csv"
)

MERCHANT_INPUT = (
    PROCESSED_DIR
    / "merchant_risk_features.csv"
)


# ----------------------------------------------------------------------
# OUTPUTS
# ----------------------------------------------------------------------

TRANSACTION_OUTPUT = (
    PROCESSED_DIR
    / "transaction_ml_anomalies.csv"
)

USER_OUTPUT = (
    PROCESSED_DIR
    / "user_ml_anomalies.csv"
)

MERCHANT_OUTPUT = (
    PROCESSED_DIR
    / "merchant_ml_anomalies.csv"
)

REPORT_OUTPUT = (
    REPORT_DIR
    / "ml_anomaly_report.json"
)


# ======================================================================
# HELPER FUNCTIONS
# ======================================================================

def numeric_value(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:

    """
    Safely convert a column to numeric.

    If the column doesn't exist, return zeros.
    """

    if column not in df.columns:

        return pd.Series(
            0.0,
            index=df.index,
            dtype=float,
        )

    return pd.to_numeric(
        df[column],
        errors="coerce",
    ).fillna(0.0)


def build_numeric_matrix(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:

    """
    Build a clean numeric feature matrix.
    """

    matrix = pd.DataFrame(
        index=df.index
    )

    for column in columns:

        matrix[column] = numeric_value(
            df,
            column,
        )

    matrix = matrix.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    matrix = matrix.fillna(0.0)

    return matrix


def run_isolation_forest(
    X: pd.DataFrame,
    contamination: float,
    random_state: int = 42,
):
    """
    Train Isolation Forest.

    Returns:
        predictions:
            1  = normal
           -1  = anomaly

        decision_scores:
            Higher = more normal
            Lower  = more anomalous
    """

    if X.empty:

        raise ValueError(
            "Feature matrix is empty."
        )

    # --------------------------------------------------------------
    # Scaling
    # --------------------------------------------------------------

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    # --------------------------------------------------------------
    # Isolation Forest
    # --------------------------------------------------------------

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )

    predictions = model.fit_predict(
        X_scaled
    )

    decision_scores = model.decision_function(
        X_scaled
    )

    return (
        predictions,
        decision_scores,
    )


def anomaly_percentile(
    anomaly_score,
    index,
) -> pd.Series:

    """
    Convert Isolation Forest decision scores
    into a 0–100 anomaly percentile.

    Lower Isolation Forest scores are more anomalous.

    Therefore:
        most anomalous → close to 100
        most normal    → close to 0
    """

    # Isolation Forest returns NumPy arrays.
    # Convert explicitly to Pandas Series and preserve index.
    score = pd.Series(
        np.asarray(anomaly_score),
        index=index,
        dtype=float,
    )

    score = pd.to_numeric(
        score,
        errors="coerce",
    ).fillna(0.0)

    # Lowest decision score = most anomalous.
    percentile = (
        score.rank(
            ascending=True,
            pct=True,
            method="average",
        )
        * 100
    )

    return percentile.round(2)


def create_anomaly_band(
    percentile: pd.Series,
) -> pd.Series:

    """
    Convert anomaly percentile into a simple
    investigator-friendly band.
    """

    return pd.Series(
        np.select(
            [
                percentile >= 95,
                percentile >= 80,
                percentile >= 50,
            ],
            [
                "HIGH",
                "MEDIUM",
                "LOW",
            ],
            default="LOW",
        ),
        index=percentile.index,
        dtype="string",
    )


# ======================================================================
# TRANSACTION ANOMALIES
# ======================================================================

def detect_transaction_anomalies(
    transactions: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\nBuilding transaction anomaly model..."
    )

    tx = transactions.copy()

    # --------------------------------------------------------------
    # Feature selection
    # --------------------------------------------------------------

    features = [
        "amount_abs",
        "amount_percentile",
        "large_amount_flag",
        "extreme_amount_flag",
        "negative_amount_flag",
        "failed_flag",
        "pending_flag",
        "chargeback_flag",
        "ticket_deviation_risk",
        "missing_utr_flag",
        "kyc_unmatched_flag",
        "merchant_unmatched_flag",
        "transaction_anomaly_score",
        "transaction_risk_score",
    ]

    X = build_numeric_matrix(
        tx,
        features,
    )

    print(
        f"✓ Transaction ML features: "
        f"{X.shape[1]}"
    )

    # --------------------------------------------------------------
    # Model
    # --------------------------------------------------------------

    predictions, decision_scores = (
        run_isolation_forest(
            X,
            contamination=0.02,
            random_state=42,
        )
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    tx["ml_anomaly_prediction"] = (
        predictions
    )

    tx["ml_decision_score"] = (
        pd.Series(
            decision_scores,
            index=tx.index,
        )
        .round(6)
    )

    tx["ml_anomaly_percentile"] = (
        anomaly_percentile(
            decision_scores,
            tx.index,
        )
    )

    tx["ml_anomaly_flag"] = (
        tx["ml_anomaly_prediction"]
        == -1
    ).astype(int)

    tx["ml_anomaly_band"] = (
        create_anomaly_band(
            tx[
                "ml_anomaly_percentile"
            ]
        )
    )

    anomaly_count = int(
        tx["ml_anomaly_flag"].sum()
    )

    print(
        f"✓ Transaction anomalies: "
        f"{anomaly_count:,}"
    )

    return tx


# ======================================================================
# USER ANOMALIES
# ======================================================================

def detect_user_anomalies(
    users: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\nBuilding user anomaly model..."
    )

    df = users.copy()

    # --------------------------------------------------------------
    # Feature selection
    # --------------------------------------------------------------

    features = [
        "transaction_count",
        "total_amount",
        "avg_transaction_amount",
        "failed_count",
        "pending_count",
        "negative_amount_count",
        "chargeback_count",
        "failure_rate",
        "pending_rate",
        "chargeback_rate",
        "activity_percentile",
        "user_risk_score",
        "identity_quality_risk",
    ]

    X = build_numeric_matrix(
        df,
        features,
    )

    print(
        f"✓ User ML features: "
        f"{X.shape[1]}"
    )

    # --------------------------------------------------------------
    # Model
    # --------------------------------------------------------------

    predictions, decision_scores = (
        run_isolation_forest(
            X,
            contamination=0.03,
            random_state=42,
        )
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    df["ml_anomaly_prediction"] = (
        predictions
    )

    df["ml_decision_score"] = (
        pd.Series(
            decision_scores,
            index=df.index,
        )
        .round(6)
    )

    df["ml_anomaly_percentile"] = (
        anomaly_percentile(
            decision_scores,
            df.index,
        )
    )

    df["ml_anomaly_flag"] = (
        df["ml_anomaly_prediction"]
        == -1
    ).astype(int)

    df["ml_anomaly_band"] = (
        create_anomaly_band(
            df[
                "ml_anomaly_percentile"
            ]
        )
    )

    anomaly_count = int(
        df["ml_anomaly_flag"].sum()
    )

    print(
        f"✓ User anomalies: "
        f"{anomaly_count:,}"
    )

    return df


# ======================================================================
# MERCHANT ANOMALIES
# ======================================================================

def detect_merchant_anomalies(
    merchants: pd.DataFrame,
) -> pd.DataFrame:

    print(
        "\nBuilding merchant anomaly model..."
    )

    df = merchants.copy()

    # --------------------------------------------------------------
    # Feature selection
    # --------------------------------------------------------------

    features = [
        "transaction_count",
        "total_amount",
        "avg_transaction_amount",
        "failed_count",
        "pending_count",
        "negative_amount_count",
        "chargeback_count",
        "failure_rate",
        "pending_rate",
        "chargeback_rate",
        "activity_percentile",
        "merchant_risk_score",
        "ticket_deviation_risk",
    ]

    X = build_numeric_matrix(
        df,
        features,
    )

    print(
        f"✓ Merchant ML features: "
        f"{X.shape[1]}"
    )

    # --------------------------------------------------------------
    # Model
    # --------------------------------------------------------------

    predictions, decision_scores = (
        run_isolation_forest(
            X,
            contamination=0.03,
            random_state=42,
        )
    )

    # --------------------------------------------------------------
    # Results
    # --------------------------------------------------------------

    df["ml_anomaly_prediction"] = (
        predictions
    )

    df["ml_decision_score"] = (
        pd.Series(
            decision_scores,
            index=df.index,
        )
        .round(6)
    )

    df["ml_anomaly_percentile"] = (
        anomaly_percentile(
            decision_scores,
            df.index,
        )
    )

    df["ml_anomaly_flag"] = (
        df["ml_anomaly_prediction"]
        == -1
    ).astype(int)

    df["ml_anomaly_band"] = (
        create_anomaly_band(
            df[
                "ml_anomaly_percentile"
            ]
        )
    )

    anomaly_count = int(
        df["ml_anomaly_flag"].sum()
    )

    print(
        f"✓ Merchant anomalies: "
        f"{anomaly_count:,}"
    )

    return df


# ======================================================================
# REPORT
# ======================================================================

def build_report(
    transaction_df: pd.DataFrame,
    user_df: pd.DataFrame,
    merchant_df: pd.DataFrame,
):

    transaction_anomalies = int(
        transaction_df[
            "ml_anomaly_flag"
        ].sum()
    )

    user_anomalies = int(
        user_df[
            "ml_anomaly_flag"
        ].sum()
    )

    merchant_anomalies = int(
        merchant_df[
            "ml_anomaly_flag"
        ].sum()
    )

    transaction_rate = (
        transaction_anomalies
        / len(transaction_df)
        * 100
        if len(transaction_df) > 0
        else 0
    )

    user_rate = (
        user_anomalies
        / len(user_df)
        * 100
        if len(user_df) > 0
        else 0
    )

    merchant_rate = (
        merchant_anomalies
        / len(merchant_df)
        * 100
        if len(merchant_df) > 0
        else 0
    )

    report = {

        "model": {
            "algorithm": "Isolation Forest",
            "learning_type": (
                "Unsupervised anomaly detection"
            ),
            "n_estimators": 200,
            "random_state": 42,

            "contamination": {
                "transactions": 0.02,
                "users": 0.03,
                "merchants": 0.03,
            },
        },

        "rows": {
            "transactions": int(
                len(transaction_df)
            ),
            "users": int(
                len(user_df)
            ),
            "merchants": int(
                len(merchant_df)
            ),
        },

        "anomalies": {
            "transactions": transaction_anomalies,
            "users": user_anomalies,
            "merchants": merchant_anomalies,
        },

        "anomaly_rates": {
            "transactions_pct": round(
                transaction_rate,
                2,
            ),
            "users_pct": round(
                user_rate,
                2,
            ),
            "merchants_pct": round(
                merchant_rate,
                2,
            ),
        },

        "notes": [
            (
                "Isolation Forest identifies "
                "observations that are unusual "
                "relative to the dataset."
            ),
            (
                "ML anomaly scores are not "
                "calibrated fraud probabilities."
            ),
            (
                "Anomaly signals should be combined "
                "with behavioral, KYC, chargeback, "
                "and network signals."
            ),
            (
                "An anomalous entity is an "
                "investigation candidate and "
                "is not automatically fraudulent."
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
        "UPI SENTINEL — ML ANOMALY DETECTION"
    )
    print("=" * 70)

    # --------------------------------------------------------------
    # Load feature tables
    # --------------------------------------------------------------

    print(
        "\nLoading feature tables..."
    )

    if not TRANSACTION_INPUT.exists():
        raise FileNotFoundError(
            f"Missing: {TRANSACTION_INPUT}"
        )

    if not USER_INPUT.exists():
        raise FileNotFoundError(
            f"Missing: {USER_INPUT}"
        )

    if not MERCHANT_INPUT.exists():
        raise FileNotFoundError(
            f"Missing: {MERCHANT_INPUT}"
        )

    transactions = pd.read_csv(
        TRANSACTION_INPUT
    )

    users = pd.read_csv(
        USER_INPUT
    )

    merchants = pd.read_csv(
        MERCHANT_INPUT
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

    # --------------------------------------------------------------
    # Transaction model
    # --------------------------------------------------------------

    transaction_result = (
        detect_transaction_anomalies(
            transactions
        )
    )

    # --------------------------------------------------------------
    # User model
    # --------------------------------------------------------------

    user_result = (
        detect_user_anomalies(
            users
        )
    )

    # --------------------------------------------------------------
    # Merchant model
    # --------------------------------------------------------------

    merchant_result = (
        detect_merchant_anomalies(
            merchants
        )
    )

    # --------------------------------------------------------------
    # Save ML tables
    # --------------------------------------------------------------

    print(
        "\nSaving ML anomaly tables..."
    )

    transaction_result.to_csv(
        TRANSACTION_OUTPUT,
        index=False,
    )

    user_result.to_csv(
        USER_OUTPUT,
        index=False,
    )

    merchant_result.to_csv(
        MERCHANT_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------------
    # Build report
    # --------------------------------------------------------------

    report = build_report(
        transaction_result,
        user_result,
        merchant_result,
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
        )

    # --------------------------------------------------------------
    # Final summary
    # --------------------------------------------------------------

    transaction_anomalies = int(
        transaction_result[
            "ml_anomaly_flag"
        ].sum()
    )

    user_anomalies = int(
        user_result[
            "ml_anomaly_flag"
        ].sum()
    )

    merchant_anomalies = int(
        merchant_result[
            "ml_anomaly_flag"
        ].sum()
    )

    print("\n" + "=" * 70)
    print(
        "ML ANOMALY DETECTION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Transaction anomalies: "
        f"{transaction_anomalies:,}"
    )

    print(
        f"User anomalies: "
        f"{user_anomalies:,}"
    )

    print(
        f"Merchant anomalies: "
        f"{merchant_anomalies:,}"
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
        f"✓ {REPORT_OUTPUT}"
    )


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    main()