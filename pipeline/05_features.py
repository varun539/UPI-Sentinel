from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# UPI SENTINEL — STAGE 05
# FEATURE ENGINEERING
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# INPUT FILES
# ============================================================

TRANSACTIONS_FILE = (
    PROCESSED_DIR / "transaction_enriched.csv"
)

USERS_FILE = (
    PROCESSED_DIR / "user_features.csv"
)

MERCHANTS_FILE = (
    PROCESSED_DIR / "merchant_features.csv"
)

CHARGEBACKS_FILE = (
    PROCESSED_DIR / "chargeback_features.csv"
)


# ============================================================
# OUTPUT FILES
# ============================================================

TRANSACTION_FEATURES_FILE = (
    PROCESSED_DIR / "transaction_features.csv"
)

USER_RISK_FEATURES_FILE = (
    PROCESSED_DIR / "user_risk_features.csv"
)

MERCHANT_RISK_FEATURES_FILE = (
    PROCESSED_DIR / "merchant_risk_features.csv"
)

FEATURE_SUMMARY_FILE = (
    REPORT_DIR / "feature_engineering_report.json"
)


# ============================================================
# HELPERS
# ============================================================

def load_csv(path):
    return pd.read_csv(
        path,
        low_memory=False,
    )


def safe_numeric(df, columns):
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    return df


def safe_divide(numerator, denominator):
    numerator = pd.to_numeric(
        numerator,
        errors="coerce",
    ).fillna(0)

    denominator = pd.to_numeric(
        denominator,
        errors="coerce",
    ).replace(
        0,
        np.nan,
    )

    return (
        numerator / denominator
    ).replace(
        [np.inf, -np.inf],
        np.nan,
    ).fillna(0)


def minmax_series(series):
    """
    Normalize a numeric series to 0-1.
    """

    series = pd.to_numeric(
        series,
        errors="coerce",
    ).fillna(0)

    if len(series) == 0:
        return pd.Series(
            0.0,
            index=series.index,
        )

    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(
            0.0,
            index=series.index,
        )

    if maximum == minimum:
        return pd.Series(
            0.0,
            index=series.index,
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    ).clip(
        0,
        1,
    )


def percentile_rank(series):
    """
    Return percentile rank between 0 and 1.
    """

    series = pd.to_numeric(
        series,
        errors="coerce",
    ).fillna(0)

    if len(series) == 0:
        return series.astype(float)

    return (
        series.rank(
            method="average",
            pct=True,
        )
        .fillna(0)
        .astype(float)
    )


def safe_binary_condition(condition):
    """
    Convert a potentially nullable boolean Series into
    a normal integer 0/1 Series.
    """

    return (
        pd.Series(
            condition,
            index=condition.index,
        )
        .fillna(False)
        .astype(bool)
        .astype(int)
    )


def ensure_transaction_flags(tx):
    """
    Make sure transaction behavioral flags exist.
    """

    tx = tx.copy()

    tx = safe_numeric(
        tx,
        ["amount"],
    )

    if "amount" not in tx.columns:
        tx["amount"] = 0.0

    if "status" in tx.columns:

        status = (
            tx["status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    else:

        status = pd.Series(
            "",
            index=tx.index,
            dtype="string",
        )

    tx["negative_amount_flag"] = safe_binary_condition(
        tx["amount"] < 0
    )

    tx["failed_flag"] = safe_binary_condition(
        status.eq("FAILED")
    )

    tx["pending_flag"] = safe_binary_condition(
        status.eq("PENDING")
    )

    if "chargeback_count" not in tx.columns:
        tx["chargeback_count"] = 0

    tx["chargeback_count"] = pd.to_numeric(
        tx["chargeback_count"],
        errors="coerce",
    ).fillna(0)

    tx["chargeback_flag"] = safe_binary_condition(
        tx["chargeback_count"] > 0
    )

    return tx


# ============================================================
# LOAD DATA
# ============================================================

def load_datasets():

    print("\nLoading analytical datasets...")

    transactions = load_csv(
        TRANSACTIONS_FILE
    )

    users = load_csv(
        USERS_FILE
    )

    merchants = load_csv(
        MERCHANTS_FILE
    )

    chargebacks = load_csv(
        CHARGEBACKS_FILE
    )

    print(
        f"✓ Transaction enriched: "
        f"{len(transactions):,}"
    )

    print(
        f"✓ User features: "
        f"{len(users):,}"
    )

    print(
        f"✓ Merchant features: "
        f"{len(merchants):,}"
    )

    print(
        f"✓ Chargeback features: "
        f"{len(chargebacks):,}"
    )

    return (
        transactions,
        users,
        merchants,
        chargebacks,
    )


# ============================================================
# TRANSACTION FEATURES
# ============================================================

def build_transaction_features(transactions):

    print(
        "\nBuilding transaction risk features..."
    )

    tx = transactions.copy()

    numeric_columns = [
        "amount",
        "chargeback_count",
        "chargeback_amount",
        "chargeback_critical_count",
        "chargeback_high_count",
        "ticket_deviation",
        "ticket_deviation_abs",
        "monthly_income",
    ]

    tx = safe_numeric(
        tx,
        numeric_columns,
    )

    if "amount" not in tx.columns:
        tx["amount"] = 0.0

    if "chargeback_count" not in tx.columns:
        tx["chargeback_count"] = 0

    if "chargeback_critical_count" not in tx.columns:
        tx["chargeback_critical_count"] = 0

    if "chargeback_high_count" not in tx.columns:
        tx["chargeback_high_count"] = 0

    tx["chargeback_count"] = (
        tx["chargeback_count"]
        .fillna(0)
    )

    tx["chargeback_critical_count"] = (
        tx["chargeback_critical_count"]
        .fillna(0)
    )

    tx["chargeback_high_count"] = (
        tx["chargeback_high_count"]
        .fillna(0)
    )

    tx = ensure_transaction_flags(tx)

    # --------------------------------------------------------
    # Amount features
    # --------------------------------------------------------

    tx["amount_abs"] = (
        tx["amount"]
        .abs()
    )

    tx["amount_zero_flag"] = safe_binary_condition(
        tx["amount"].fillna(0).eq(0)
    )

    tx["amount_percentile"] = (
        percentile_rank(
            tx["amount_abs"]
        )
    )

    tx["large_amount_flag"] = safe_binary_condition(
        tx["amount_percentile"].ge(0.95)
    )

    tx["extreme_amount_flag"] = safe_binary_condition(
        tx["amount_percentile"].ge(0.99)
    )

    # --------------------------------------------------------
    # Timestamp features
    # --------------------------------------------------------

    if "timestamp" in tx.columns:

        parsed_timestamp = pd.to_datetime(
            tx["timestamp"],
            errors="coerce",
        )

        tx["txn_hour"] = (
            parsed_timestamp.dt.hour
        )

        tx["txn_day_of_week"] = (
            parsed_timestamp.dt.dayofweek
        )

        tx["txn_date"] = (
            parsed_timestamp
            .dt.date
            .astype("string")
        )

        tx["weekend_flag"] = safe_binary_condition(
            parsed_timestamp
            .dt.dayofweek
            .isin([5, 6])
        )

        tx["night_transaction_flag"] = safe_binary_condition(
            parsed_timestamp
            .dt.hour
            .isin([0, 1, 2, 3, 4, 5])
        )

        tx["late_evening_flag"] = safe_binary_condition(
            parsed_timestamp
            .dt.hour
            .isin([22, 23])
        )

    else:

        tx["txn_hour"] = np.nan
        tx["txn_day_of_week"] = np.nan
        tx["txn_date"] = ""
        tx["weekend_flag"] = 0
        tx["night_transaction_flag"] = 0
        tx["late_evening_flag"] = 0

    # --------------------------------------------------------
    # Ticket deviation
    # --------------------------------------------------------

    if "ticket_deviation_abs" in tx.columns:

        tx["ticket_deviation_risk"] = (
            minmax_series(
                tx["ticket_deviation_abs"]
            )
        )

    else:

        tx["ticket_deviation_risk"] = 0.0

    # --------------------------------------------------------
    # Chargeback signals
    # --------------------------------------------------------

    tx["chargeback_risk_flag"] = (
        tx["chargeback_flag"]
        .fillna(0)
        .astype(int)
    )

    tx["critical_chargeback_flag"] = safe_binary_condition(
        tx["chargeback_critical_count"] > 0
    )

    tx["high_chargeback_flag"] = safe_binary_condition(
        tx["chargeback_high_count"] > 0
    )

    # --------------------------------------------------------
    # Relationship / data-quality signals
    # --------------------------------------------------------

    if "kyc_match_flag" in tx.columns:

        tx["kyc_unmatched_flag"] = safe_binary_condition(
            pd.to_numeric(
                tx["kyc_match_flag"],
                errors="coerce",
            ).fillna(0).eq(0)
        )

    else:

        tx["kyc_unmatched_flag"] = 0

    if "merchant_match_flag" in tx.columns:

        tx["merchant_unmatched_flag"] = safe_binary_condition(
            pd.to_numeric(
                tx["merchant_match_flag"],
                errors="coerce",
            ).fillna(0).eq(0)
        )

    else:

        tx["merchant_unmatched_flag"] = 0

    if "utr" in tx.columns:

        tx["missing_utr_flag"] = safe_binary_condition(
            tx["utr"].isna()
        )

    else:

        tx["missing_utr_flag"] = 0

    # --------------------------------------------------------
    # Transaction anomaly score
    # --------------------------------------------------------

    tx["transaction_anomaly_score"] = (
        (
            0.25
            * tx["large_amount_flag"]
        )
        +
        (
            0.20
            * tx["negative_amount_flag"]
        )
        +
        (
            0.15
            * tx["failed_flag"]
        )
        +
        (
            0.10
            * tx["pending_flag"]
        )
        +
        (
            0.15
            * tx["chargeback_risk_flag"]
        )
        +
        (
            0.15
            * tx["ticket_deviation_risk"]
        )
    ).clip(
        0,
        1,
    )

    tx["transaction_risk_score"] = (
        tx["transaction_anomaly_score"]
        * 100
    ).round(2)

    print(
        f"✓ Transaction features: "
        f"{len(tx):,}"
    )

    return tx


# ============================================================
# USER RISK FEATURES
# ============================================================

def build_user_risk_features(users):

    print(
        "\nBuilding user risk features..."
    )

    user = users.copy()

    numeric_columns = [
        "txn_count",
        "total_transaction_value",
        "avg_transaction_value",
        "median_transaction_value",
        "unique_merchants",
        "unique_mcc",
        "failed_txn_count",
        "pending_txn_count",
        "negative_amount_count",
        "failed_txn_rate",
        "pending_txn_rate",
        "negative_amount_rate",
        "chargeback_count",
        "chargeback_amount",
        "critical_chargeback_count",
        "high_chargeback_count",
        "chargeback_rate",
        "pan_valid_flag",
        "aadhaar_valid_flag",
        "aadhaar_masked_flag",
    ]

    user = safe_numeric(
        user,
        numeric_columns,
    )

    # Ensure expected numeric columns exist.
    defaults = {
        "txn_count": 0,
        "total_transaction_value": 0,
        "avg_transaction_value": 0,
        "median_transaction_value": 0,
        "unique_merchants": 0,
        "unique_mcc": 0,
        "failed_txn_count": 0,
        "pending_txn_count": 0,
        "negative_amount_count": 0,
        "failed_txn_rate": 0,
        "pending_txn_rate": 0,
        "negative_amount_rate": 0,
        "chargeback_count": 0,
        "chargeback_amount": 0,
        "critical_chargeback_count": 0,
        "high_chargeback_count": 0,
        "chargeback_rate": 0,
        "pan_valid_flag": 0,
        "aadhaar_valid_flag": 0,
        "aadhaar_masked_flag": 0,
    }

    for column, default in defaults.items():

        if column not in user.columns:
            user[column] = default

        user[column] = (
            user[column]
            .fillna(default)
        )

    # --------------------------------------------------------
    # Activity
    # --------------------------------------------------------

    user["txn_count_percentile"] = (
        percentile_rank(
            user["txn_count"]
        )
    )

    user["transaction_value_percentile"] = (
        percentile_rank(
            user["total_transaction_value"]
            .abs()
        )
    )

    user["merchant_diversity_percentile"] = (
        percentile_rank(
            user["unique_merchants"]
        )
    )

    # --------------------------------------------------------
    # Behavioral flags
    # --------------------------------------------------------

    user["high_failure_behavior_flag"] = safe_binary_condition(
        user["failed_txn_rate"].ge(0.20)
    )

    user["high_pending_behavior_flag"] = safe_binary_condition(
        user["pending_txn_rate"].ge(0.15)
    )

    user["negative_amount_behavior_flag"] = safe_binary_condition(
        user["negative_amount_rate"].gt(0)
    )

    user["high_chargeback_behavior_flag"] = safe_binary_condition(
        user["chargeback_rate"].ge(0.05)
    )

    user["critical_chargeback_flag"] = safe_binary_condition(
        user["critical_chargeback_count"].gt(0)
    )

    # --------------------------------------------------------
    # KYC signals
    # --------------------------------------------------------

    if "kyc_high_risk_flag" not in user.columns:

        if "risk_segment" in user.columns:

            risk_segment = (
                user["risk_segment"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

            user["kyc_high_risk_flag"] = safe_binary_condition(
                risk_segment.eq("HIGH")
            )

        else:

            user["kyc_high_risk_flag"] = 0

    else:

        user["kyc_high_risk_flag"] = (
            pd.to_numeric(
                user["kyc_high_risk_flag"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

    if "kyc_verified_flag" not in user.columns:

        if "kyc_status" in user.columns:

            kyc_status = (
                user["kyc_status"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

            user["kyc_verified_flag"] = safe_binary_condition(
                kyc_status.eq("VERIFIED")
            )

        else:

            user["kyc_verified_flag"] = 0

    else:

        user["kyc_verified_flag"] = (
            pd.to_numeric(
                user["kyc_verified_flag"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

    user["kyc_risk_signal"] = (
        user["kyc_high_risk_flag"]
        +
        (
            1
            -
            user["kyc_verified_flag"]
        )
    ).clip(
        0,
        1,
    )

    # --------------------------------------------------------
    # Identity quality
    # --------------------------------------------------------

    user["identity_quality_risk"] = (
        (
            1
            -
            user["pan_valid_flag"]
            .clip(0, 1)
        )
        +
        (
            1
            -
            user["aadhaar_valid_flag"]
            .clip(0, 1)
        )
    ) / 2

    # --------------------------------------------------------
    # Risk components
    # --------------------------------------------------------

    failure_component = (
        user["failed_txn_rate"]
        .clip(0, 1)
    )

    pending_component = (
        user["pending_txn_rate"]
        .clip(0, 1)
    )

    negative_component = (
        user["negative_amount_rate"]
        .clip(0, 1)
    )

    chargeback_component = (
        user["chargeback_rate"]
        .clip(0, 1)
    )

    activity_component = (
        0.5
        * user["txn_count_percentile"]
        +
        0.5
        * user["transaction_value_percentile"]
    ).clip(
        0,
        1,
    )

    # --------------------------------------------------------
    # User risk score
    # --------------------------------------------------------

    user["user_risk_score"] = (
        (
            0.20
            * failure_component
        )
        +
        (
            0.10
            * pending_component
        )
        +
        (
            0.10
            * negative_component
        )
        +
        (
            0.20
            * chargeback_component
        )
        +
        (
            0.15
            * user["kyc_risk_signal"]
        )
        +
        (
            0.10
            * user["identity_quality_risk"]
        )
        +
        (
            0.15
            * activity_component
        )
    ).clip(
        0,
        1,
    )

    user["user_risk_score"] = (
        user["user_risk_score"]
        * 100
    ).round(2)

    user["risk_band"] = pd.cut(
        user["user_risk_score"],
        bins=[
            -np.inf,
            25,
            50,
            75,
            np.inf,
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        ],
    ).astype("string")

    print(
        f"✓ User risk features: "
        f"{len(user):,}"
    )

    return user


# ============================================================
# MERCHANT RISK FEATURES
# ============================================================

def build_merchant_risk_features(merchants):

    print(
        "\nBuilding merchant risk features..."
    )

    merchant = merchants.copy()

    numeric_columns = [
        "txn_count",
        "total_transaction_value",
        "avg_transaction_value",
        "unique_users",
        "unique_mcc",
        "failed_txn_count",
        "pending_txn_count",
        "negative_amount_count",
        "failure_rate",
        "pending_rate",
        "negative_amount_rate",
        "chargeback_count",
        "chargeback_amount",
        "critical_chargeback_count",
        "high_chargeback_count",
        "chargeback_rate",
        "declared_avg_ticket_size",
        "ticket_deviation",
        "ticket_deviation_abs",
    ]

    merchant = safe_numeric(
        merchant,
        numeric_columns,
    )

    # --------------------------------------------------------
    # Ensure numeric columns exist
    # --------------------------------------------------------

    defaults = {
        "txn_count": 0,
        "total_transaction_value": 0,
        "avg_transaction_value": 0,
        "unique_users": 0,
        "unique_mcc": 0,
        "failed_txn_count": 0,
        "pending_txn_count": 0,
        "negative_amount_count": 0,
        "failure_rate": 0,
        "pending_rate": 0,
        "negative_amount_rate": 0,
        "chargeback_count": 0,
        "chargeback_amount": 0,
        "critical_chargeback_count": 0,
        "high_chargeback_count": 0,
        "chargeback_rate": 0,
        "declared_avg_ticket_size": 0,
        "ticket_deviation": 0,
        "ticket_deviation_abs": 0,
    }

    for column, default in defaults.items():

        if column not in merchant.columns:
            merchant[column] = default

        merchant[column] = (
            merchant[column]
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .fillna(default)
        )

    # --------------------------------------------------------
    # Activity metrics
    # --------------------------------------------------------

    merchant["txn_count_percentile"] = (
        percentile_rank(
            merchant["txn_count"]
        )
    )

    merchant["user_count_percentile"] = (
        percentile_rank(
            merchant["unique_users"]
        )
    )

    merchant["transaction_value_percentile"] = (
        percentile_rank(
            merchant[
                "total_transaction_value"
            ].abs()
        )
    )

    # --------------------------------------------------------
    # Behavioral signals
    # --------------------------------------------------------

    merchant["high_failure_flag"] = safe_binary_condition(
        merchant["failure_rate"].ge(0.20)
    )

    merchant["high_pending_flag"] = safe_binary_condition(
        merchant["pending_rate"].ge(0.15)
    )

    merchant["negative_transaction_flag"] = safe_binary_condition(
        merchant["negative_amount_rate"].gt(0)
    )

    merchant["high_chargeback_flag"] = safe_binary_condition(
        merchant["chargeback_rate"].ge(0.05)
    )

    merchant["critical_chargeback_flag"] = safe_binary_condition(
        merchant["critical_chargeback_count"].gt(0)
    )

    # --------------------------------------------------------
    # Merchant status
    # --------------------------------------------------------

    if "merchant_status" in merchant.columns:

        status = (
            merchant["merchant_status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        merchant["suspended_flag"] = safe_binary_condition(
            status.eq("SUSPENDED")
        )

        merchant["blocked_flag"] = safe_binary_condition(
            status.eq("BLOCKED")
        )

        merchant["inactive_flag"] = safe_binary_condition(
            status.eq("INACTIVE")
        )

    else:

        merchant["suspended_flag"] = 0
        merchant["blocked_flag"] = 0
        merchant["inactive_flag"] = 0

    # --------------------------------------------------------
    # Merchant match quality
    # --------------------------------------------------------

    if "merchant_match_flag" in merchant.columns:

        merchant["merchant_match_flag"] = (
            pd.to_numeric(
                merchant["merchant_match_flag"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

    else:

        merchant["merchant_match_flag"] = 0

    # --------------------------------------------------------
    # Ticket deviation
    # --------------------------------------------------------

    merchant["ticket_deviation_risk"] = (
        minmax_series(
            merchant["ticket_deviation_abs"]
        )
    )

    # --------------------------------------------------------
    # Merchant network intensity
    # --------------------------------------------------------

    merchant["user_to_txn_ratio"] = safe_divide(
        merchant["unique_users"],
        merchant["txn_count"],
    )

    merchant["high_user_concentration_flag"] = safe_binary_condition(
        merchant["user_count_percentile"].ge(0.95)
    )

    # --------------------------------------------------------
    # Risk components
    # --------------------------------------------------------

    failure_component = (
        merchant["failure_rate"]
        .clip(0, 1)
    )

    pending_component = (
        merchant["pending_rate"]
        .clip(0, 1)
    )

    negative_component = (
        merchant["negative_amount_rate"]
        .clip(0, 1)
    )

    chargeback_component = (
        merchant["chargeback_rate"]
        .clip(0, 1)
    )

    status_component = (
        merchant[
            [
                "suspended_flag",
                "blocked_flag",
            ]
        ]
        .fillna(0)
        .max(axis=1)
    )

    activity_component = (
        0.5
        * merchant["txn_count_percentile"]
        +
        0.5
        * merchant["transaction_value_percentile"]
    ).clip(
        0,
        1,
    )

    # --------------------------------------------------------
    # Merchant risk score
    # --------------------------------------------------------

    merchant["merchant_risk_score"] = (
        (
            0.20
            * failure_component
        )
        +
        (
            0.10
            * pending_component
        )
        +
        (
            0.10
            * negative_component
        )
        +
        (
            0.25
            * chargeback_component
        )
        +
        (
            0.15
            * merchant[
                "ticket_deviation_risk"
            ]
        )
        +
        (
            0.10
            * status_component
        )
        +
        (
            0.10
            * activity_component
        )
    ).clip(
        0,
        1,
    )

    merchant["merchant_risk_score"] = (
        merchant["merchant_risk_score"]
        * 100
    ).round(2)

    merchant["risk_band"] = pd.cut(
        merchant["merchant_risk_score"],
        bins=[
            -np.inf,
            25,
            50,
            75,
            np.inf,
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        ],
    ).astype("string")

    print(
        f"✓ Merchant risk features: "
        f"{len(merchant):,}"
    )

    return merchant


# ============================================================
# CROSS-ENTITY FEATURES
# ============================================================

def build_cross_entity_features(
    transaction_features,
    user_features,
    merchant_features,
):

    print(
        "\nBuilding cross-entity risk features..."
    )

    tx = transaction_features.copy()

    # --------------------------------------------------------
    # User risk
    # --------------------------------------------------------

    user_risk_columns = [
        "user_id",
        "user_risk_score",
        "risk_band",
    ]

    user_risk_columns = [
        column
        for column in user_risk_columns
        if column in user_features.columns
    ]

    if user_risk_columns:

        user_join = user_features[
            user_risk_columns
        ].copy()

        user_join = user_join.rename(
            columns={
                "user_risk_score":
                    "transaction_user_risk_score",
                "risk_band":
                    "transaction_user_risk_band",
            }
        )

        tx = tx.merge(
            user_join,
            on="user_id",
            how="left",
            validate="many_to_one",
        )

    # --------------------------------------------------------
    # Merchant risk
    # --------------------------------------------------------

    merchant_risk_columns = [
        "merchant_id",
        "merchant_risk_score",
        "risk_band",
    ]

    merchant_risk_columns = [
        column
        for column in merchant_risk_columns
        if column in merchant_features.columns
    ]

    if merchant_risk_columns:

        merchant_join = merchant_features[
            merchant_risk_columns
        ].copy()

        merchant_join = merchant_join.rename(
            columns={
                "merchant_risk_score":
                    "transaction_merchant_risk_score",
                "risk_band":
                    "transaction_merchant_risk_band",
            }
        )

        tx = tx.merge(
            merchant_join,
            on="merchant_id",
            how="left",
            validate="many_to_one",
        )

    # --------------------------------------------------------
    # Combined risk
    # --------------------------------------------------------

    if "transaction_user_risk_score" in tx.columns:

        user_score = (
            pd.to_numeric(
                tx[
                    "transaction_user_risk_score"
                ],
                errors="coerce",
            )
            .fillna(0)
        )

    else:

        user_score = pd.Series(
            0.0,
            index=tx.index,
        )

    if "transaction_merchant_risk_score" in tx.columns:

        merchant_score = (
            pd.to_numeric(
                tx[
                    "transaction_merchant_risk_score"
                ],
                errors="coerce",
            )
            .fillna(0)
        )

    else:

        merchant_score = pd.Series(
            0.0,
            index=tx.index,
        )

    transaction_score = (
        pd.to_numeric(
            tx["transaction_risk_score"],
            errors="coerce",
        )
        .fillna(0)
    )

    tx["combined_risk_score"] = (
        (
            0.40
            * transaction_score
        )
        +
        (
            0.30
            * user_score
        )
        +
        (
            0.30
            * merchant_score
        )
    ).clip(
        0,
        100,
    ).round(2)

    tx["combined_risk_band"] = pd.cut(
        tx["combined_risk_score"],
        bins=[
            -np.inf,
            25,
            50,
            75,
            np.inf,
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        ],
    ).astype("string")

    print(
        f"✓ Cross-entity features: "
        f"{len(tx):,}"
    )

    return tx


# ============================================================
# FEATURE REPORT
# ============================================================

def build_feature_report(
    transaction_features,
    user_features,
    merchant_features,
):

    report = {}

    # --------------------------------------------------------
    # Row counts
    # --------------------------------------------------------

    report["rows"] = {
        "transaction_features": int(
            len(transaction_features)
        ),
        "user_risk_features": int(
            len(user_features)
        ),
        "merchant_risk_features": int(
            len(merchant_features)
        ),
    }

    # --------------------------------------------------------
    # Risk distributions
    # --------------------------------------------------------

    if "combined_risk_band" in transaction_features.columns:

        report[
            "transaction_risk_distribution"
        ] = {
            str(key): int(value)
            for key, value in (
                transaction_features[
                    "combined_risk_band"
                ]
                .value_counts(
                    dropna=False
                )
                .to_dict()
                .items()
            )
        }

    if "risk_band" in user_features.columns:

        report[
            "user_risk_distribution"
        ] = {
            str(key): int(value)
            for key, value in (
                user_features[
                    "risk_band"
                ]
                .value_counts(
                    dropna=False
                )
                .to_dict()
                .items()
            )
        }

    if "risk_band" in merchant_features.columns:

        report[
            "merchant_risk_distribution"
        ] = {
            str(key): int(value)
            for key, value in (
                merchant_features[
                    "risk_band"
                ]
                .value_counts(
                    dropna=False
                )
                .to_dict()
                .items()
            )
        }

    # --------------------------------------------------------
    # High-risk counts
    # --------------------------------------------------------

    report["high_risk_counts"] = {
        "transactions": int(
            (
                transaction_features[
                    "combined_risk_score"
                ]
                >= 75
            ).sum()
        ),

        "users": int(
            (
                user_features[
                    "user_risk_score"
                ]
                >= 75
            ).sum()
        ),

        "merchants": int(
            (
                merchant_features[
                    "merchant_risk_score"
                ]
                >= 75
            ).sum()
        ),
    }

    # --------------------------------------------------------
    # Feature inventory
    # --------------------------------------------------------

    report["feature_counts"] = {
        "transaction_features": int(
            len(transaction_features.columns)
        ),
        "user_features": int(
            len(user_features.columns)
        ),
        "merchant_features": int(
            len(merchant_features.columns)
        ),
    }

    return report


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print(
        "UPI SENTINEL — FEATURE ENGINEERING"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        transactions,
        users,
        merchants,
        chargebacks,
    ) = load_datasets()

    # --------------------------------------------------------
    # Transaction features
    # --------------------------------------------------------

    transaction_features = (
        build_transaction_features(
            transactions
        )
    )

    # --------------------------------------------------------
    # User features
    # --------------------------------------------------------

    user_risk_features = (
        build_user_risk_features(
            users
        )
    )

    # --------------------------------------------------------
    # Merchant features
    # --------------------------------------------------------

    merchant_risk_features = (
        build_merchant_risk_features(
            merchants
        )
    )

    # --------------------------------------------------------
    # Cross entity enrichment
    # --------------------------------------------------------

    transaction_features = (
        build_cross_entity_features(
            transaction_features,
            user_risk_features,
            merchant_risk_features,
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    print(
        "\nSaving feature tables..."
    )

    transaction_features.to_csv(
        TRANSACTION_FEATURES_FILE,
        index=False,
    )

    user_risk_features.to_csv(
        USER_RISK_FEATURES_FILE,
        index=False,
    )

    merchant_risk_features.to_csv(
        MERCHANT_RISK_FEATURES_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    report = build_feature_report(
        transaction_features,
        user_risk_features,
        merchant_risk_features,
    )

    with open(
        FEATURE_SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            default=str,
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "FEATURE ENGINEERING COMPLETE"
    )
    print("=" * 70)

    print(
        f"Transaction feature rows: "
        f"{len(transaction_features):,}"
    )

    print(
        f"User risk feature rows: "
        f"{len(user_risk_features):,}"
    )

    print(
        f"Merchant risk feature rows: "
        f"{len(merchant_risk_features):,}"
    )

    print(
        f"Transaction feature columns: "
        f"{len(transaction_features.columns):,}"
    )

    print(
        f"User feature columns: "
        f"{len(user_risk_features.columns):,}"
    )

    print(
        f"Merchant feature columns: "
        f"{len(merchant_risk_features.columns):,}"
    )

    print("\nHigh-risk entities:")

    print(
        f"  Transactions: "
        f"{report['high_risk_counts']['transactions']:,}"
    )

    print(
        f"  Users: "
        f"{report['high_risk_counts']['users']:,}"
    )

    print(
        f"  Merchants: "
        f"{report['high_risk_counts']['merchants']:,}"
    )

    print(
        f"\nFeature report: "
        f"{FEATURE_SUMMARY_FILE}"
    )

    print(
        f"Feature tables: "
        f"{PROCESSED_DIR}"
    )


if __name__ == "__main__":
    main()