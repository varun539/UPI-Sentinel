from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

TRANSACTIONS_FILE = PROCESSED_DIR / "upi_transactions_clean.csv"
KYC_FILE = PROCESSED_DIR / "kyc_records_clean.csv"
MERCHANTS_FILE = PROCESSED_DIR / "merchants_clean.csv"
CHARGEBACKS_FILE = PROCESSED_DIR / "chargebacks_clean.csv"


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


def rate(numerator, denominator):
    """
    Safe percentage/rate calculation.
    """
    denominator = denominator.replace(0, np.nan)

    result = numerator / denominator

    return result.fillna(0)


def ensure_transaction_flags(tx):
    """
    Make sure transaction behavioral flags exist.

    This is intentionally defensive because the cleaned CSV
    may not contain every analytical flag depending on which
    version of the cleaning pipeline generated it.
    """

    tx = tx.copy()

    # Amount must be numeric.
    tx = safe_numeric(
        tx,
        ["amount"],
    )

    # Transaction status normalization.
    if "status" in tx.columns:
        tx["status"] = (
            tx["status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )
    else:
        tx["status"] = ""

    # Behavioral flags.
    tx["negative_amount_flag"] = (
        tx["amount"] < 0
    ).astype(int)

    tx["failed_flag"] = (
        tx["status"] == "FAILED"
    ).astype(int)

    tx["pending_flag"] = (
        tx["status"] == "PENDING"
    ).astype(int)

    return tx


# ============================================================
# LOAD DATA
# ============================================================

def load_datasets():

    print("\nLoading cleaned datasets...")

    transactions = load_csv(
        TRANSACTIONS_FILE
    )

    kyc = load_csv(
        KYC_FILE
    )

    merchants = load_csv(
        MERCHANTS_FILE
    )

    chargebacks = load_csv(
        CHARGEBACKS_FILE
    )

    print(
        f"✓ Transactions: {len(transactions):,}"
    )

    print(
        f"✓ KYC records: {len(kyc):,}"
    )

    print(
        f"✓ Merchants: {len(merchants):,}"
    )

    print(
        f"✓ Chargebacks: {len(chargebacks):,}"
    )

    return (
        transactions,
        kyc,
        merchants,
        chargebacks,
    )


# ============================================================
# CANONICAL ENTITY TABLES
# ============================================================

def build_canonical_kyc(kyc):
    """
    KYC can contain multiple records for the same user.

    Create one analytical user record by selecting the most
    informative/latest record.

    Priority:
    1. Higher completeness
    2. Latest signup timestamp
    """

    print("\nBuilding canonical KYC entity table...")

    df = kyc.copy()

    completeness_columns = [
        "full_name",
        "pan",
        "aadhaar",
        "date_of_birth",
        "city",
        "state",
        "monthly_income",
        "occupation",
        "signup_timestamp",
        "kyc_status",
        "risk_segment",
    ]

    available_columns = [
        c
        for c in completeness_columns
        if c in df.columns
    ]

    df["_completeness_score"] = (
        df[available_columns]
        .notna()
        .sum(axis=1)
    )

    if "signup_timestamp" in df.columns:

        df["_signup_sort"] = pd.to_datetime(
            df["signup_timestamp"],
            errors="coerce",
        )

    else:

        df["_signup_sort"] = pd.NaT

    df = df.sort_values(
        [
            "user_id",
            "_completeness_score",
            "_signup_sort",
        ],
        ascending=[
            True,
            False,
            False,
        ],
    )

    df = (
        df.drop_duplicates(
            subset=["user_id"],
            keep="first",
        )
        .copy()
    )

    df = df.drop(
        columns=[
            "_completeness_score",
            "_signup_sort",
        ],
        errors="ignore",
    )

    print(
        f"✓ Canonical users: {len(df):,}"
    )

    return df


def build_canonical_merchants(merchants):
    """
    Merchant master can contain multiple records per merchant ID.

    Select the most complete/latest analytical record.
    """

    print("\nBuilding canonical merchant entity table...")

    df = merchants.copy()

    completeness_columns = [
        "merchant_name",
        "mcc",
        "merchant_category",
        "business_type",
        "city",
        "state",
        "onboarding_date",
        "settlement_account",
        "merchant_status",
        "declared_avg_ticket_size",
    ]

    available_columns = [
        c
        for c in completeness_columns
        if c in df.columns
    ]

    df["_completeness_score"] = (
        df[available_columns]
        .notna()
        .sum(axis=1)
    )

    if "onboarding_date" in df.columns:

        df["_onboarding_sort"] = pd.to_datetime(
            df["onboarding_date"],
            errors="coerce",
        )

    else:

        df["_onboarding_sort"] = pd.NaT

    df = df.sort_values(
        [
            "merchant_id",
            "_completeness_score",
            "_onboarding_sort",
        ],
        ascending=[
            True,
            False,
            False,
        ],
    )

    df = (
        df.drop_duplicates(
            subset=["merchant_id"],
            keep="first",
        )
        .copy()
    )

    df = df.drop(
        columns=[
            "_completeness_score",
            "_onboarding_sort",
        ],
        errors="ignore",
    )

    print(
        f"✓ Canonical merchants: {len(df):,}"
    )

    return df


# ============================================================
# CHARGEBACK AGGREGATION
# ============================================================

def build_chargeback_features(chargebacks):
    """
    Aggregate chargeback behavior at:
    - transaction
    - user
    - merchant
    levels.
    """

    print("\nBuilding chargeback features...")

    cb = chargebacks.copy()

    cb = safe_numeric(
        cb,
        ["disputed_amount"],
    )

    # Make sure severity flags exist.
    if "severity" in cb.columns:

        cb["severity"] = (
            cb["severity"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    else:

        cb["severity"] = ""

    cb["critical_flag"] = (
        cb["severity"] == "CRITICAL"
    ).astype(int)

    cb["high_flag"] = (
        cb["severity"] == "HIGH"
    ).astype(int)

    # --------------------------------------------------------
    # Transaction-level chargebacks
    # --------------------------------------------------------

    transaction_cb = (
        cb[cb["txn_id"].notna()]
        .groupby("txn_id")
        .agg(
            chargeback_count=(
                "complaint_id",
                "count",
            ),
            chargeback_amount=(
                "disputed_amount",
                "sum",
            ),
            chargeback_critical_count=(
                "critical_flag",
                "sum",
            ),
            chargeback_high_count=(
                "high_flag",
                "sum",
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # User-level chargebacks
    # --------------------------------------------------------

    user_cb = (
        cb.groupby("user_id")
        .agg(
            chargeback_count=(
                "complaint_id",
                "count",
            ),
            chargeback_amount=(
                "disputed_amount",
                "sum",
            ),
            critical_chargeback_count=(
                "critical_flag",
                "sum",
            ),
            high_chargeback_count=(
                "high_flag",
                "sum",
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Merchant-level chargebacks
    # --------------------------------------------------------

    merchant_cb = (
        cb.groupby("merchant_id")
        .agg(
            chargeback_count=(
                "complaint_id",
                "count",
            ),
            chargeback_amount=(
                "disputed_amount",
                "sum",
            ),
            critical_chargeback_count=(
                "critical_flag",
                "sum",
            ),
            high_chargeback_count=(
                "high_flag",
                "sum",
            ),
        )
        .reset_index()
    )

    print(
        f"✓ Transaction chargeback entities: "
        f"{len(transaction_cb):,}"
    )

    print(
        f"✓ User chargeback entities: "
        f"{len(user_cb):,}"
    )

    print(
        f"✓ Merchant chargeback entities: "
        f"{len(merchant_cb):,}"
    )

    return (
        transaction_cb,
        user_cb,
        merchant_cb,
    )


# ============================================================
# TRANSACTION ENRICHMENT
# ============================================================

def build_transaction_enriched(
    transactions,
    canonical_kyc,
    canonical_merchants,
    transaction_cb,
):
    """
    Build the main analytical transaction table.

    IMPORTANT:
    LEFT JOIN from transactions.

    Therefore ALL transactions remain.
    """

    print("\nBuilding transaction_enriched...")

    tx = transactions.copy()

    # Ensure numeric amount and status.
    tx = safe_numeric(
        tx,
        ["amount"],
    )

    if "status" in tx.columns:

        tx["status"] = (
            tx["status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    # --------------------------------------------------------
    # User enrichment
    # --------------------------------------------------------

    kyc_columns = [
        "user_id",
        "kyc_status",
        "risk_segment",
        "pan_valid_flag",
        "aadhaar_valid_flag",
        "aadhaar_masked_flag",
        "date_of_birth",
        "monthly_income",
        "city",
        "state",
        "occupation",
    ]

    kyc_columns = [
        c
        for c in kyc_columns
        if c in canonical_kyc.columns
    ]

    kyc_join = canonical_kyc[
        kyc_columns
    ].copy()

    kyc_join = kyc_join.rename(
        columns={
            "risk_segment": "kyc_risk_segment",
            "city": "user_city",
            "state": "user_state",
            "occupation": "user_occupation",
        }
    )

    tx = tx.merge(
        kyc_join,
        on="user_id",
        how="left",
        validate="many_to_one",
    )

    # --------------------------------------------------------
    # Merchant enrichment
    # --------------------------------------------------------

    merchant_columns = [
        "merchant_id",
        "merchant_name",
        "mcc",
        "merchant_category",
        "business_type",
        "city",
        "state",
        "onboarding_date",
        "merchant_status",
        "declared_avg_ticket_size",
    ]

    merchant_columns = [
        c
        for c in merchant_columns
        if c in canonical_merchants.columns
    ]

    merchant_join = canonical_merchants[
        merchant_columns
    ].copy()

    merchant_join = merchant_join.rename(
        columns={
            "mcc": "merchant_mcc",
            "city": "merchant_city",
            "state": "merchant_state",
        }
    )

    tx = tx.merge(
        merchant_join,
        on="merchant_id",
        how="left",
        validate="many_to_one",
    )

    # --------------------------------------------------------
    # Chargeback enrichment
    # --------------------------------------------------------

    tx = tx.merge(
        transaction_cb,
        on="txn_id",
        how="left",
        validate="one_to_one",
    )

    chargeback_numeric_columns = [
        "chargeback_count",
        "chargeback_amount",
        "chargeback_critical_count",
        "chargeback_high_count",
    ]

    for column in chargeback_numeric_columns:

        if column in tx.columns:

            tx[column] = tx[column].fillna(0)

    # --------------------------------------------------------
    # Relationship flags
    # --------------------------------------------------------

    if "kyc_status" in tx.columns:

        tx["kyc_match_flag"] = (
            tx["kyc_status"].notna()
        ).astype(int)

    else:

        tx["kyc_match_flag"] = 0

    if "merchant_name" in tx.columns:

        tx["merchant_match_flag"] = (
            tx["merchant_name"].notna()
        ).astype(int)

    else:

        tx["merchant_match_flag"] = 0

    tx["chargeback_flag"] = (
        tx["chargeback_count"] > 0
    ).astype(int)

    # --------------------------------------------------------
    # Transaction behavior flags
    # --------------------------------------------------------

    tx["large_transaction_flag"] = (
        tx["amount"]
        > tx["amount"].quantile(0.95)
    ).astype(int)

    tx["negative_amount_flag"] = (
        tx["amount"] < 0
    ).astype(int)

    tx["failed_flag"] = (
        tx["status"] == "FAILED"
    ).astype(int)

    tx["pending_flag"] = (
        tx["status"] == "PENDING"
    ).astype(int)

    # --------------------------------------------------------
    # Merchant ticket deviation
    # --------------------------------------------------------

    tx["ticket_deviation"] = np.nan

    if "declared_avg_ticket_size" in tx.columns:

        tx = safe_numeric(
            tx,
            ["declared_avg_ticket_size"],
        )

        valid_ticket = (
            tx["declared_avg_ticket_size"].notna()
            & (
                tx["declared_avg_ticket_size"] > 0
            )
        )

        tx.loc[
            valid_ticket,
            "ticket_deviation",
        ] = (
            (
                tx.loc[
                    valid_ticket,
                    "amount",
                ]
                - tx.loc[
                    valid_ticket,
                    "declared_avg_ticket_size",
                ]
            )
            /
            tx.loc[
                valid_ticket,
                "declared_avg_ticket_size",
            ]
        )

    tx["ticket_deviation_abs"] = (
        tx["ticket_deviation"]
        .abs()
    )

    print(
        f"✓ Enriched transactions: "
        f"{len(tx):,}"
    )

    return tx


# ============================================================
# USER FEATURES
# ============================================================

def build_user_features(
    transactions,
    canonical_kyc,
    user_cb,
):
    """
    Aggregate transaction behavior at user level.
    """

    print("\nBuilding user_features...")

    tx = ensure_transaction_flags(
        transactions
    )

    user = (
        tx.groupby("user_id")
        .agg(
            txn_count=(
                "txn_id",
                "count",
            ),
            total_transaction_value=(
                "amount",
                "sum",
            ),
            avg_transaction_value=(
                "amount",
                "mean",
            ),
            median_transaction_value=(
                "amount",
                "median",
            ),
            unique_merchants=(
                "merchant_id",
                "nunique",
            ),
            unique_mcc=(
                "mcc",
                "nunique",
            ),
            failed_txn_count=(
                "failed_flag",
                "sum",
            ),
            pending_txn_count=(
                "pending_flag",
                "sum",
            ),
            negative_amount_count=(
                "negative_amount_flag",
                "sum",
            ),
        )
        .reset_index()
    )

    user["failed_txn_rate"] = rate(
        user["failed_txn_count"],
        user["txn_count"],
    )

    user["pending_txn_rate"] = rate(
        user["pending_txn_count"],
        user["txn_count"],
    )

    user["negative_amount_rate"] = rate(
        user["negative_amount_count"],
        user["txn_count"],
    )

    # --------------------------------------------------------
    # Chargebacks
    # --------------------------------------------------------

    user = user.merge(
        user_cb,
        on="user_id",
        how="left",
        validate="one_to_one",
    )

    for column in [
        "chargeback_count",
        "chargeback_amount",
        "critical_chargeback_count",
        "high_chargeback_count",
    ]:

        if column in user.columns:

            user[column] = user[column].fillna(0)

    user["chargeback_rate"] = rate(
        user["chargeback_count"],
        user["txn_count"],
    )

    # --------------------------------------------------------
    # KYC
    # --------------------------------------------------------

    kyc_columns = [
        "user_id",
        "kyc_status",
        "risk_segment",
        "pan_valid_flag",
        "aadhaar_valid_flag",
        "aadhaar_masked_flag",
        "monthly_income",
        "city",
        "state",
    ]

    kyc_columns = [
        c
        for c in kyc_columns
        if c in canonical_kyc.columns
    ]

    user = user.merge(
        canonical_kyc[kyc_columns],
        on="user_id",
        how="left",
        validate="one_to_one",
    )

    if "kyc_status" in user.columns:

        user["kyc_match_flag"] = (
            user["kyc_status"].notna()
        ).astype(int)

        user["kyc_verified_flag"] = (
            user["kyc_status"] == "VERIFIED"
        ).astype(int)

    else:

        user["kyc_match_flag"] = 0
        user["kyc_verified_flag"] = 0

    if "risk_segment" in user.columns:

        user["kyc_high_risk_flag"] = (
            user["risk_segment"] == "HIGH"
        ).astype(int)

    else:

        user["kyc_high_risk_flag"] = 0

    print(
        f"✓ User features: "
        f"{len(user):,}"
    )

    return user


# ============================================================
# MERCHANT FEATURES
# ============================================================

def build_merchant_features(
    transactions,
    canonical_merchants,
    merchant_cb,
):
    """
    Aggregate transaction behavior at merchant level.

    IMPORTANT:
    The transaction CSV may not contain analytical flags.
    Therefore we explicitly create them before aggregation.
    """

    print("\nBuilding merchant_features...")

    # --------------------------------------------------------
    # FIX:
    # Create all required behavioral flags before groupby.
    # --------------------------------------------------------

    tx = ensure_transaction_flags(
        transactions
    )

    # --------------------------------------------------------
    # Merchant aggregation
    # --------------------------------------------------------

    merchant = (
        tx.groupby("merchant_id")
        .agg(
            txn_count=(
                "txn_id",
                "count",
            ),
            total_transaction_value=(
                "amount",
                "sum",
            ),
            avg_transaction_value=(
                "amount",
                "mean",
            ),
            unique_users=(
                "user_id",
                "nunique",
            ),
            unique_mcc=(
                "mcc",
                "nunique",
            ),
            failed_txn_count=(
                "failed_flag",
                "sum",
            ),
            pending_txn_count=(
                "pending_flag",
                "sum",
            ),
            negative_amount_count=(
                "negative_amount_flag",
                "sum",
            ),
        )
        .reset_index()
    )

    merchant["failure_rate"] = rate(
        merchant["failed_txn_count"],
        merchant["txn_count"],
    )

    merchant["pending_rate"] = rate(
        merchant["pending_txn_count"],
        merchant["txn_count"],
    )

    merchant["negative_amount_rate"] = rate(
        merchant["negative_amount_count"],
        merchant["txn_count"],
    )

    # --------------------------------------------------------
    # Chargebacks
    # --------------------------------------------------------

    merchant = merchant.merge(
        merchant_cb,
        on="merchant_id",
        how="left",
        validate="one_to_one",
    )

    for column in [
        "chargeback_count",
        "chargeback_amount",
        "critical_chargeback_count",
        "high_chargeback_count",
    ]:

        if column in merchant.columns:

            merchant[column] = merchant[column].fillna(0)

    merchant["chargeback_rate"] = rate(
        merchant["chargeback_count"],
        merchant["txn_count"],
    )

    # --------------------------------------------------------
    # Merchant master
    # --------------------------------------------------------

    master_columns = [
        "merchant_id",
        "merchant_name",
        "merchant_category",
        "business_type",
        "city",
        "state",
        "merchant_status",
        "declared_avg_ticket_size",
        "mcc",
    ]

    master_columns = [
        c
        for c in master_columns
        if c in canonical_merchants.columns
    ]

    master = canonical_merchants[
        master_columns
    ].copy()

    master = master.rename(
        columns={
            "mcc": "master_mcc",
            "city": "merchant_city",
            "state": "merchant_state",
        }
    )

    merchant = merchant.merge(
        master,
        on="merchant_id",
        how="left",
        validate="many_to_one",
    )

    merchant["merchant_match_flag"] = (
        merchant["merchant_name"].notna()
    ).astype(int)

    merchant["suspended_flag"] = (
        merchant["merchant_status"]
        == "SUSPENDED"
    ).astype(int)

    merchant["blocked_flag"] = (
        merchant["merchant_status"]
        == "BLOCKED"
    ).astype(int)

    # --------------------------------------------------------
    # Actual vs declared ticket size
    # --------------------------------------------------------

    merchant["ticket_deviation"] = np.nan

    if "declared_avg_ticket_size" in merchant.columns:

        merchant = safe_numeric(
            merchant,
            ["declared_avg_ticket_size"],
        )

        valid_ticket = (
            merchant["declared_avg_ticket_size"].notna()
            & (
                merchant["declared_avg_ticket_size"] > 0
            )
        )

        merchant.loc[
            valid_ticket,
            "ticket_deviation",
        ] = (
            (
                merchant.loc[
                    valid_ticket,
                    "avg_transaction_value",
                ]
                -
                merchant.loc[
                    valid_ticket,
                    "declared_avg_ticket_size",
                ]
            )
            /
            merchant.loc[
                valid_ticket,
                "declared_avg_ticket_size",
            ]
        )

    merchant["ticket_deviation_abs"] = (
        merchant["ticket_deviation"]
        .abs()
    )

    print(
        f"✓ Merchant features: "
        f"{len(merchant):,}"
    )

    return merchant


# ============================================================
# CHARGEBACK FEATURES
# ============================================================

def build_chargeback_summary(chargebacks):
    """
    Create a clean analytical chargeback table.
    """

    print("\nBuilding chargeback_features...")

    cb = chargebacks.copy()

    cb = safe_numeric(
        cb,
        ["disputed_amount"],
    )

    # --------------------------------------------------------
    # Timing metrics
    # --------------------------------------------------------

    if {
        "transaction_timestamp",
        "reported_timestamp",
    }.issubset(cb.columns):

        cb["report_delay_hours"] = (
            (
                pd.to_datetime(
                    cb["reported_timestamp"],
                    errors="coerce",
                )
                -
                pd.to_datetime(
                    cb["transaction_timestamp"],
                    errors="coerce",
                )
            )
            .dt.total_seconds()
            / 3600
        )

    if {
        "reported_timestamp",
        "bank_response_timestamp",
    }.issubset(cb.columns):

        cb["bank_response_delay_hours"] = (
            (
                pd.to_datetime(
                    cb["bank_response_timestamp"],
                    errors="coerce",
                )
                -
                pd.to_datetime(
                    cb["reported_timestamp"],
                    errors="coerce",
                )
            )
            .dt.total_seconds()
            / 3600
        )

    print(
        f"✓ Chargeback features: "
        f"{len(cb):,}"
    )

    return cb


# ============================================================
# REPORT
# ============================================================

def build_transform_report(
    transactions,
    transaction_enriched,
    user_features,
    merchant_features,
    chargeback_features,
):
    report = {
        "input_transactions": int(
            len(transactions)
        ),

        "output_transactions": int(
            len(transaction_enriched)
        ),

        "unique_users": int(
            user_features["user_id"].nunique()
        ),

        "unique_merchants": int(
            merchant_features["merchant_id"].nunique()
        ),

        "chargeback_records": int(
            len(chargeback_features)
        ),

        "transaction_kyc_match_rate_pct": round(
            transaction_enriched[
                "kyc_match_flag"
            ].mean()
            * 100,
            2,
        ),

        "transaction_merchant_match_rate_pct": round(
            transaction_enriched[
                "merchant_match_flag"
            ].mean()
            * 100,
            2,
        ),

        "transactions_with_chargeback_pct": round(
            transaction_enriched[
                "chargeback_flag"
            ].mean()
            * 100,
            2,
        ),
    }

    return report


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("UPI SENTINEL — ANALYTICAL TRANSFORMATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        transactions,
        kyc,
        merchants,
        chargebacks,
    ) = load_datasets()

    # --------------------------------------------------------
    # Canonical entities
    # --------------------------------------------------------

    canonical_kyc = build_canonical_kyc(
        kyc
    )

    canonical_merchants = build_canonical_merchants(
        merchants
    )

    # --------------------------------------------------------
    # Chargeback aggregations
    # --------------------------------------------------------

    (
        transaction_cb,
        user_cb,
        merchant_cb,
    ) = build_chargeback_features(
        chargebacks
    )

    # --------------------------------------------------------
    # Main transaction table
    # --------------------------------------------------------

    transaction_enriched = (
        build_transaction_enriched(
            transactions,
            canonical_kyc,
            canonical_merchants,
            transaction_cb,
        )
    )

    # --------------------------------------------------------
    # User features
    # --------------------------------------------------------

    user_features = build_user_features(
        transactions,
        canonical_kyc,
        user_cb,
    )

    # --------------------------------------------------------
    # Merchant features
    # --------------------------------------------------------

    merchant_features = build_merchant_features(
        transactions,
        canonical_merchants,
        merchant_cb,
    )

    # --------------------------------------------------------
    # Chargeback analytical table
    # --------------------------------------------------------

    chargeback_features = (
        build_chargeback_summary(
            chargebacks
        )
    )

    # --------------------------------------------------------
    # Save outputs
    # --------------------------------------------------------

    print("\nSaving analytical tables...")

    transaction_enriched.to_csv(
        PROCESSED_DIR
        / "transaction_enriched.csv",
        index=False,
    )

    user_features.to_csv(
        PROCESSED_DIR
        / "user_features.csv",
        index=False,
    )

    merchant_features.to_csv(
        PROCESSED_DIR
        / "merchant_features.csv",
        index=False,
    )

    chargeback_features.to_csv(
        PROCESSED_DIR
        / "chargeback_features.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    report = build_transform_report(
        transactions,
        transaction_enriched,
        user_features,
        merchant_features,
        chargeback_features,
    )

    report_path = (
        REPORT_DIR
        / "transform_report.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("ANALYTICAL TRANSFORMATION COMPLETE")
    print("=" * 70)

    print(
        f"Transactions: "
        f"{len(transaction_enriched):,}"
    )

    print(
        f"Users: "
        f"{len(user_features):,}"
    )

    print(
        f"Merchants: "
        f"{len(merchant_features):,}"
    )

    print(
        f"Chargebacks: "
        f"{len(chargeback_features):,}"
    )

    print(
        "\nRelationship coverage:"
    )

    print(
        f"  Transaction → KYC: "
        f"{report['transaction_kyc_match_rate_pct']:.2f}%"
    )

    print(
        f"  Transaction → Merchant: "
        f"{report['transaction_merchant_match_rate_pct']:.2f}%"
    )

    print(
        f"  Transactions with chargeback: "
        f"{report['transactions_with_chargeback_pct']:.2f}%"
    )

    print(
        f"\nTransform report: "
        f"{report_path}"
    )

    print(
        f"Analytical data: "
        f"{PROCESSED_DIR}"
    )


if __name__ == "__main__":
    main()