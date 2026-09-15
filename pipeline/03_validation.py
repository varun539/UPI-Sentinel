from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def load_csv(filename):
    return pd.read_csv(
        PROCESSED_DIR / filename,
        low_memory=False,
    )


def percentage(value, total):
    if total == 0:
        return 0.0

    return round(
        (value / total) * 100,
        2,
    )


def unique_count(df, column):
    return int(
        df[column]
        .dropna()
        .nunique()
    )


def duplicate_count(df, column):
    series = df[column].dropna()

    return int(
        series.duplicated().sum()
    )


# ============================================================
# TRANSACTIONS
# ============================================================

def validate_transactions(df):

    amount = pd.to_numeric(
        df["amount"],
        errors="coerce",
    )

    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    return {
        "rows": len(df),
        "unique_txn_ids": unique_count(
            df,
            "txn_id",
        ),
        "duplicate_txn_ids": duplicate_count(
            df,
            "txn_id",
        ),
        "missing_txn_id": int(
            df["txn_id"].isna().sum()
        ),
        "missing_user_id": int(
            df["user_id"].isna().sum()
        ),
        "missing_merchant_id": int(
            df["merchant_id"].isna().sum()
        ),
        "missing_utr": int(
            df["utr"].isna().sum()
        ),
        "duplicate_utr_count": int(
            df["utr"]
            .dropna()
            .duplicated()
            .sum()
        ),
        "missing_mcc": int(
            df["mcc"].isna().sum()
        ),
        "missing_timestamp": int(
            timestamps.isna().sum()
        ),
        "missing_amount": int(
            amount.isna().sum()
        ),
        "negative_amount": int(
            (amount < 0).sum()
        ),
        "zero_amount": int(
            (amount == 0).sum()
        ),
        "amount_min": float(
            amount.min()
        ),
        "amount_max": float(
            amount.max()
        ),
        "amount_median": float(
            amount.median()
        ),
        "timestamp_min": (
            timestamps.min().isoformat()
            if timestamps.notna().any()
            else None
        ),
        "timestamp_max": (
            timestamps.max().isoformat()
            if timestamps.notna().any()
            else None
        ),
        "status_distribution": (
            df["status"]
            .fillna("MISSING")
            .value_counts()
            .to_dict()
        ),
        "unique_mcc_count": int(
            df["mcc"].nunique(
                dropna=True
            )
        ),
    }


# ============================================================
# KYC
# ============================================================

def validate_kyc(df):

    income = pd.to_numeric(
        df["monthly_income"],
        errors="coerce",
    )

    # PAN validation only on non-missing values.
    pan = (
        df["pan"]
        .dropna()
        .astype(str)
        .str.upper()
    )

    valid_pan = pan.str.fullmatch(
        r"[A-Z]{5}[0-9]{4}[A-Z]"
    )

    # Aadhaar validation only on non-missing
    # and non-masked values.
    aadhaar = (
        df["aadhaar"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    masked_aadhaar = aadhaar.str.contains(
        "X",
        case=False,
        na=False,
    )

    numeric_aadhaar = aadhaar[
        ~masked_aadhaar
    ]

    valid_aadhaar = numeric_aadhaar.str.fullmatch(
        r"\d{12}"
    )

    return {
        "rows": len(df),
        "unique_user_ids": unique_count(
            df,
            "user_id",
        ),
        "duplicate_user_ids": duplicate_count(
            df,
            "user_id",
        ),
        "missing_user_id": int(
            df["user_id"].isna().sum()
        ),
        "missing_pan": int(
            df["pan"].isna().sum()
        ),
        "invalid_pan_format": int(
            (~valid_pan).sum()
        ),
        "missing_aadhaar": int(
            df["aadhaar"].isna().sum()
        ),
        "masked_aadhaar": int(
            masked_aadhaar.sum()
        ),
        "invalid_aadhaar_format": int(
            (~valid_aadhaar).sum()
        ),
        "missing_date_of_birth": int(
            df["date_of_birth"].isna().sum()
        ),
        "missing_income": int(
            income.isna().sum()
        ),
        "negative_income": int(
            (income < 0).sum()
        ),
        "zero_income": int(
            (income == 0).sum()
        ),
        "income_min": float(
            income.min()
        ),
        "income_max": float(
            income.max()
        ),
        "kyc_status_distribution": (
            df["kyc_status"]
            .fillna("MISSING")
            .value_counts()
            .to_dict()
        ),
        "risk_segment_distribution": (
            df["risk_segment"]
            .fillna("MISSING")
            .value_counts()
            .to_dict()
        ),
    }


# ============================================================
# MERCHANTS
# ============================================================

def validate_merchants(df):

    ticket = pd.to_numeric(
        df["declared_avg_ticket_size"],
        errors="coerce",
    )

    return {
        "rows": len(df),
        "unique_merchant_ids": unique_count(
            df,
            "merchant_id",
        ),
        "duplicate_merchant_ids": duplicate_count(
            df,
            "merchant_id",
        ),
        "missing_merchant_id": int(
            df["merchant_id"].isna().sum()
        ),
        "missing_mcc": int(
            df["mcc"].isna().sum()
        ),
        "missing_onboarding_date": int(
            df["onboarding_date"].isna().sum()
        ),
        "missing_settlement_account": int(
            df["settlement_account"].isna().sum()
        ),
        "missing_declared_avg_ticket_size": int(
            ticket.isna().sum()
        ),
        "negative_declared_avg_ticket_size": int(
            (ticket < 0).sum()
        ),
        "ticket_size_min": float(
            ticket.min()
        ),
        "ticket_size_max": float(
            ticket.max()
        ),
        "merchant_status_distribution": (
            df["merchant_status"]
            .fillna("MISSING")
            .value_counts()
            .to_dict()
        ),
        "merchant_category_count": int(
            df["merchant_category"]
            .nunique(
                dropna=True
            )
        ),
    }


# ============================================================
# CHARGEBACKS
# ============================================================

def validate_chargebacks(df):

    disputed = pd.to_numeric(
        df["disputed_amount"],
        errors="coerce",
    )

    transaction_time = pd.to_datetime(
        df["transaction_timestamp"],
        errors="coerce",
    )

    reported_time = pd.to_datetime(
        df["reported_timestamp"],
        errors="coerce",
    )

    bank_time = pd.to_datetime(
        df["bank_response_timestamp"],
        errors="coerce",
    )

    comparable_reported = (
        transaction_time.notna()
        & reported_time.notna()
    )

    comparable_bank = (
        reported_time.notna()
        & bank_time.notna()
    )

    return {
        "rows": len(df),
        "unique_complaint_ids": unique_count(
            df,
            "complaint_id",
        ),
        "duplicate_complaint_ids": duplicate_count(
            df,
            "complaint_id",
        ),
        "missing_complaint_id": int(
            df["complaint_id"].isna().sum()
        ),
        "missing_txn_id": int(
            df["txn_id"].isna().sum()
        ),
        "missing_user_id": int(
            df["user_id"].isna().sum()
        ),
        "missing_merchant_id": int(
            df["merchant_id"].isna().sum()
        ),
        "missing_disputed_amount": int(
            disputed.isna().sum()
        ),
        "negative_disputed_amount": int(
            (disputed < 0).sum()
        ),
        "total_disputed_amount": float(
            disputed.sum()
        ),
        "transaction_timestamp_missing": int(
            transaction_time.isna().sum()
        ),
        "reported_timestamp_missing": int(
            reported_time.isna().sum()
        ),
        "bank_response_timestamp_missing": int(
            bank_time.isna().sum()
        ),
        "reported_before_transaction": int(
            (
                reported_time[comparable_reported]
                < transaction_time[comparable_reported]
            ).sum()
        ),
        "bank_response_before_reported": int(
            (
                bank_time[comparable_bank]
                < reported_time[comparable_bank]
            ).sum()
        ),
        "severity_distribution": (
            df["severity"]
            .fillna("MISSING")
            .value_counts()
            .to_dict()
        ),
    }


# ============================================================
# RELATIONSHIPS
# ============================================================

def relationship_check(
    source,
    source_column,
    target,
    target_column,
):

    source_values = (
        source[source_column]
        .dropna()
        .astype(str)
    )

    target_values = set(
        target[target_column]
        .dropna()
        .astype(str)
    )

    matched = source_values.isin(
        target_values
    )

    total = len(source_values)
    matched_count = int(
        matched.sum()
    )

    return {
        "source_rows_with_key": total,
        "matched_rows": matched_count,
        "unmatched_rows": int(
            total - matched_count
        ),
        "match_rate_pct": percentage(
            matched_count,
            total,
        ),
    }


def validate_relationships(
    transactions,
    kyc,
    merchants,
    chargebacks,
):

    return {
        "transaction_to_kyc": relationship_check(
            transactions,
            "user_id",
            kyc,
            "user_id",
        ),

        "transaction_to_merchant": relationship_check(
            transactions,
            "merchant_id",
            merchants,
            "merchant_id",
        ),

        "chargeback_to_transaction": relationship_check(
            chargebacks,
            "txn_id",
            transactions,
            "txn_id",
        ),

        "chargeback_to_kyc": relationship_check(
            chargebacks,
            "user_id",
            kyc,
            "user_id",
        ),

        "chargeback_to_merchant": relationship_check(
            chargebacks,
            "merchant_id",
            merchants,
            "merchant_id",
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("UPI SENTINEL — DATA VALIDATION")
    print("=" * 60)

    print("\nLoading processed datasets...")

    transactions = load_csv(
        "upi_transactions_clean.csv"
    )

    kyc = load_csv(
        "kyc_records_clean.csv"
    )

    merchants = load_csv(
        "merchants_clean.csv"
    )

    chargebacks = load_csv(
        "chargebacks_clean.csv"
    )

    print("✓ Transactions loaded")
    print("✓ KYC loaded")
    print("✓ Merchants loaded")
    print("✓ Chargebacks loaded")

    print("\nRunning dataset-level validation...")

    report = {
        "transactions": validate_transactions(
            transactions
        ),

        "kyc": validate_kyc(
            kyc
        ),

        "merchants": validate_merchants(
            merchants
        ),

        "chargebacks": validate_chargebacks(
            chargebacks
        ),
    }

    print("✓ Transaction validation complete")
    print("✓ KYC validation complete")
    print("✓ Merchant validation complete")
    print("✓ Chargeback validation complete")

    print("\nRunning cross-dataset integrity checks...")

    report["relationships"] = validate_relationships(
        transactions,
        kyc,
        merchants,
        chargebacks,
    )

    print("✓ Relationship validation complete")

    output_path = (
        REPORT_DIR /
        "validation_report.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)

    print(
        f"\nValidation report: {output_path}"
    )

    print("\nKey relationship coverage:")

    for name, values in report[
        "relationships"
    ].items():

        print(
            f"  {name}: "
            f"{values['match_rate_pct']}%"
        )


if __name__ == "__main__":
    main()