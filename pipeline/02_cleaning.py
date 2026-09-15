from pathlib import Path
import json
import re

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# GENERIC HELPERS
# ============================================================

def clean_text(value):
    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if not value or value.lower() in {"nan", "none", "null", "nat"}:
        return pd.NA

    return re.sub(r"\s+", " ", value)


def normalize_id(value, remove_hyphen=False):
    """
    Canonicalize identifier values.

    Rules:
    - trim whitespace
    - uppercase
    - remove internal whitespace
    - optionally remove hyphens

    We use remove_hyphen=True for merchant IDs because
    the merchant master contains values such as MCH-2637,
    while transactions contain MCH2637.
    """
    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if not value or value.lower() in {"nan", "none", "null", "nat"}:
        return pd.NA

    value = re.sub(r"\s+", "", value).upper()

    if remove_hyphen:
        value = value.replace("-", "")

    return value


def clean_amount(value):
    """
    Parse currency values while preserving negative values.

    Examples:
        ₹1,250.50
        Rs. 1250
        INR 1250
        $1,250
        -23820.57
    """
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "null"}:
        return pd.NA

    cleaned = re.sub(r"[^0-9.\-]", "", text)

    if cleaned in {"", "-", ".", "-."}:
        return pd.NA

    # Protect against malformed strings containing
    # multiple decimal points.
    if cleaned.count(".") > 1:
        parts = cleaned.split(".")
        cleaned = parts[0] + "." + "".join(parts[1:])

    try:
        return float(cleaned)
    except ValueError:
        return pd.NA


def normalize_status(value, mapping):
    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    if not value:
        return pd.NA

    return mapping.get(value, value)


def clean_mcc(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().upper()

    if not text or text in {"NAN", "NONE", "NULL"}:
        return pd.NA

    digits = re.sub(r"\D", "", text)

    if not digits:
        return pd.NA

    if len(digits) >= 4:
        return digits[-4:]

    return digits.zfill(4)


# ============================================================
# TIMESTAMP CLEANING
# ============================================================

TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",

    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",

    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %I:%M:%S %p",
    "%d/%m/%Y %I:%M %p",
    "%d/%m/%Y",

    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y",

    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%d-%m-%Y %I:%M:%S %p",
    "%d-%m-%Y %I:%M %p",
    "%d-%m-%Y",

    "%m-%d-%Y %H:%M:%S",
    "%m-%d-%Y %H:%M",
    "%m-%d-%Y %I:%M:%S %p",
    "%m-%d-%Y %I:%M %p",
    "%m-%d-%Y",

    "%d-%b-%Y %H:%M:%S",
    "%d-%b-%Y %H:%M",
    "%d-%b-%Y %I:%M:%S %p",
    "%d-%b-%Y %I:%M %p",
    "%d-%b-%Y",

    "%d %b %Y %H:%M:%S",
    "%d %b %Y %H:%M",
    "%d %b %Y %I:%M:%S %p",
    "%d %b %Y %I:%M %p",
    "%d %b %Y",

    "%Y%m%d",
]


def parse_single_timestamp(value):
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()

    if not text or text.lower() in {
        "nan",
        "none",
        "null",
        "nat",
    }:
        return pd.NaT

    # --------------------------------------------------------
    # Unix timestamp: 9-10 digit seconds
    #
    # 9-digit timestamps are important for the messy DOB data.
    # --------------------------------------------------------
    if re.fullmatch(r"\d{9,10}", text):
        try:
            result = pd.to_datetime(
                int(text),
                unit="s",
                errors="coerce",
            )

            if not pd.isna(result):
                return result
        except (ValueError, OverflowError):
            pass

    # --------------------------------------------------------
    # Unix milliseconds
    # --------------------------------------------------------
    if re.fullmatch(r"\d{13}", text):
        try:
            result = pd.to_datetime(
                int(text),
                unit="ms",
                errors="coerce",
            )

            if not pd.isna(result):
                return result
        except (ValueError, OverflowError):
            pass

    # --------------------------------------------------------
    # Explicit formats
    # --------------------------------------------------------
    for fmt in TIMESTAMP_FORMATS:
        try:
            result = pd.to_datetime(
                text,
                format=fmt,
                errors="coerce",
            )

            if not pd.isna(result):
                return result

        except (ValueError, TypeError):
            continue

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------
    try:
        result = pd.to_datetime(
            text,
            errors="coerce",
            dayfirst=False,
        )

        if not pd.isna(result):
            return result

    except (ValueError, TypeError):
        pass

    return pd.NaT


def clean_timestamp(series):
    return series.apply(parse_single_timestamp)


# ============================================================
# VALIDATION HELPERS
# ============================================================

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def normalize_pan(value):
    value = clean_text(value)

    if pd.isna(value):
        return pd.NA

    return (
        str(value)
        .upper()
        .replace(" ", "")
        .replace("-", "")
    )


def validate_pan(value):
    if pd.isna(value):
        return False

    return bool(PAN_PATTERN.fullmatch(str(value)))


def normalize_aadhaar(value):
    value = clean_text(value)

    if pd.isna(value):
        return pd.NA

    return (
        str(value)
        .upper()
        .replace(" ", "")
        .replace("-", "")
    )


def is_masked_aadhaar(value):
    if pd.isna(value):
        return False

    return bool(re.fullmatch(r"X{4,12}", str(value)))


def validate_aadhaar(value):
    if pd.isna(value):
        return False

    value = str(value)

    if "X" in value:
        return False

    return bool(re.fullmatch(r"\d{12}", value))


# ============================================================
# STATUS MAPS
# ============================================================

TXN_STATUS_MAP = {
    "SUCCESS": "SUCCESS",
    "TXN_SUCCESS": "SUCCESS",
    "COMPLETED": "SUCCESS",
    "S": "SUCCESS",

    "FAILED": "FAILED",
    "TXN_FAILED": "FAILED",
    "FAIL": "FAILED",
    "DECLINED": "FAILED",
    "F": "FAILED",

    "PENDING": "PENDING",
    "PROCESSING": "PENDING",
    "INITIATED": "PENDING",
}


KYC_STATUS_MAP = {
    "VERIFIED": "VERIFIED",
    "APPROVED": "VERIFIED",
    "KYC_DONE": "VERIFIED",
    "V": "VERIFIED",
    "DONE": "VERIFIED",

    "PENDING": "PENDING",
    "P": "PENDING",

    "REJECTED": "REJECTED",
    "REJECT": "REJECTED",
    "R": "REJECTED",

    "FAILED": "FAILED",
    "IN_PROGRESS": "IN_PROGRESS",
    "UNDER REVIEW": "UNDER_REVIEW",
}


MERCHANT_STATUS_MAP = {
    "ACTIVE": "ACTIVE",
    "ENABLED": "ACTIVE",
    "LIVE": "ACTIVE",
    "A": "ACTIVE",

    "INACTIVE": "INACTIVE",
    "DISABLED": "INACTIVE",
    "CLOSED": "INACTIVE",
    "I": "INACTIVE",

    "SUSPENDED": "SUSPENDED",
    "S": "SUSPENDED",

    "HOLD": "HOLD",
    "BLOCKED": "BLOCKED",
}


SEVERITY_MAP = {
    "P1": "CRITICAL",
    "CRITICAL": "CRITICAL",
    "CRIT": "CRITICAL",

    "P2": "HIGH",
    "HIGH": "HIGH",
    "H": "HIGH",

    "P3": "MEDIUM",
    "MEDIUM": "MEDIUM",
    "M": "MEDIUM",

    "P4": "LOW",
    "LOW": "LOW",
    "L": "LOW",
}


# ============================================================
# LOADERS
# ============================================================

def load_csv(path):
    return pd.read_csv(path, low_memory=False)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return pd.json_normalize(json.load(file))


# ============================================================
# TRANSACTIONS
# ============================================================

def clean_transactions():

    df = load_csv(
        RAW_DIR / "track1_upi_transactions.csv"
    )

    raw_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())

    # Preserve raw IDs for auditability.
    for column in [
        "txn_id",
        "user_id",
        "merchant_id",
        "utr",
    ]:
        df[f"{column}_raw"] = df[column]

    # Canonical identifiers.
    df["txn_id"] = df["txn_id"].apply(
        normalize_id
    )

    df["user_id"] = df["user_id"].apply(
        normalize_id
    )

    # Merchant IDs are canonicalized across datasets.
    df["merchant_id"] = df["merchant_id"].apply(
        lambda x: normalize_id(x, remove_hyphen=True)
    )

    df["utr"] = df["utr"].apply(
        normalize_id
    )

    # Timestamp.
    df["timestamp"] = clean_timestamp(
        df["timestamp"]
    )

    # Amount.
    df["amount"] = df["amount"].apply(
        clean_amount
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce",
    )

    # MCC.
    df["mcc"] = df["mcc"].apply(
        clean_mcc
    )

    # Status.
    df["status"] = df["status"].apply(
        lambda x: normalize_status(
            x,
            TXN_STATUS_MAP,
        )
    )

    # --------------------------------------------------------
    # Data-quality flags
    # --------------------------------------------------------

    df["amount_negative_flag"] = (
        df["amount"] < 0
    ).astype(int)

    df["utr_missing_flag"] = (
        df["utr"].isna()
    ).astype(int)

    df["mcc_missing_flag"] = (
        df["mcc"].isna()
    ).astype(int)

    df["amount_missing_flag"] = (
        df["amount"].isna()
    ).astype(int)

    df["timestamp_missing_flag"] = (
        df["timestamp"].isna()
    ).astype(int)

    df["failed_flag"] = (
        df["status"] == "FAILED"
    ).astype(int)

    df["pending_flag"] = (
        df["status"] == "PENDING"
    ).astype(int)

    # Remove exact duplicates after normalization.
    df = df.drop_duplicates().reset_index(
        drop=True
    )

    output_path = (
        PROCESSED_DIR /
        "upi_transactions_clean.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return {
        "dataset": "upi_transactions",
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "exact_duplicates_removed": exact_duplicates,
        "missing_utr": int(df["utr"].isna().sum()),
        "missing_mcc": int(df["mcc"].isna().sum()),
        "missing_timestamp": int(
            df["timestamp"].isna().sum()
        ),
        "missing_amount": int(
            df["amount"].isna().sum()
        ),
        "negative_amount": int(
            (df["amount"] < 0).sum()
        ),
    }


# ============================================================
# KYC
# ============================================================

def clean_kyc():

    df = load_csv(
        RAW_DIR / "track1_kyc_records.csv"
    )

    raw_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())

    df["user_id_raw"] = df["user_id"]

    df["user_id"] = df["user_id"].apply(
        normalize_id
    )

    for column in [
        "full_name",
        "city",
        "state",
        "occupation",
    ]:
        df[column] = df[column].apply(
            clean_text
        )

    # PAN.
    df["pan"] = df["pan"].apply(
        normalize_pan
    )

    df["pan_valid_flag"] = (
        df["pan"].apply(validate_pan)
    ).astype(int)

    df["pan_invalid_flag"] = (
        (
            df["pan"].notna()
            & (df["pan_valid_flag"] == 0)
        )
    ).astype(int)

    # Aadhaar.
    df["aadhaar"] = df["aadhaar"].apply(
        normalize_aadhaar
    )

    df["aadhaar_masked_flag"] = (
        df["aadhaar"].apply(is_masked_aadhaar)
    ).astype(int)

    df["aadhaar_valid_flag"] = (
        df["aadhaar"].apply(validate_aadhaar)
    ).astype(int)

    df["aadhaar_invalid_flag"] = (
        (
            df["aadhaar"].notna()
            & (df["aadhaar_masked_flag"] == 0)
            & (df["aadhaar_valid_flag"] == 0)
        )
    ).astype(int)

    # DOB.
    df["date_of_birth"] = clean_timestamp(
        df["date_of_birth"]
    )

    # Income.
    df["monthly_income"] = (
        df["monthly_income"]
        .apply(clean_amount)
    )

    df["monthly_income"] = pd.to_numeric(
        df["monthly_income"],
        errors="coerce",
    )

    # Signup timestamp.
    df["signup_timestamp"] = clean_timestamp(
        df["signup_timestamp"]
    )

    # Status.
    df["kyc_status"] = df["kyc_status"].apply(
        lambda x: normalize_status(
            x,
            KYC_STATUS_MAP,
        )
    )

    # Risk.
    df["risk_segment"] = (
        df["risk_segment"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    # --------------------------------------------------------
    # Data-quality flags
    # --------------------------------------------------------

    df["income_negative_flag"] = (
        df["monthly_income"] < 0
    ).astype(int)

    df["dob_missing_flag"] = (
        df["date_of_birth"].isna()
    ).astype(int)

    df["income_missing_flag"] = (
        df["monthly_income"].isna()
    ).astype(int)

    df["signup_timestamp_missing_flag"] = (
        df["signup_timestamp"].isna()
    ).astype(int)

    df["kyc_verified_flag"] = (
        df["kyc_status"] == "VERIFIED"
    ).astype(int)

    df["kyc_high_risk_flag"] = (
        df["risk_segment"] == "HIGH"
    ).astype(int)

    # Remove exact duplicates.
    df = df.drop_duplicates().reset_index(
        drop=True
    )

    output_path = (
        PROCESSED_DIR /
        "kyc_records_clean.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return {
        "dataset": "kyc_records",
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "exact_duplicates_removed": exact_duplicates,
        "missing_user_id": int(
            df["user_id"].isna().sum()
        ),
        "missing_pan": int(
            df["pan"].isna().sum()
        ),
        "invalid_pan_format": int(
            df["pan_invalid_flag"].sum()
        ),
        "missing_aadhaar": int(
            df["aadhaar"].isna().sum()
        ),
        "masked_aadhaar": int(
            df["aadhaar_masked_flag"].sum()
        ),
        "invalid_aadhaar_format": int(
            df["aadhaar_invalid_flag"].sum()
        ),
        "missing_date_of_birth": int(
            df["date_of_birth"].isna().sum()
        ),
        "missing_income": int(
            df["monthly_income"].isna().sum()
        ),
        "negative_income": int(
            (df["monthly_income"] < 0).sum()
        ),
        "missing_signup_timestamp": int(
            df["signup_timestamp"].isna().sum()
        ),
    }


# ============================================================
# MERCHANTS
# ============================================================

def clean_merchants():

    df = load_csv(
        RAW_DIR / "track1_merchants_master.csv"
    )

    raw_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())

    df["merchant_id_raw"] = df["merchant_id"]

    # IMPORTANT:
    # Canonicalize merchant IDs so:
    # MCH-2637 == MCH2637
    df["merchant_id"] = df["merchant_id"].apply(
        lambda x: normalize_id(
            x,
            remove_hyphen=True,
        )
    )

    for column in [
        "merchant_name",
        "merchant_category",
        "business_type",
        "city",
        "state",
        "settlement_account",
    ]:
        df[column] = df[column].apply(
            clean_text
        )

    df["mcc"] = df["mcc"].apply(
        clean_mcc
    )

    df["onboarding_date"] = clean_timestamp(
        df["onboarding_date"]
    )

    df["declared_avg_ticket_size"] = (
        df["declared_avg_ticket_size"]
        .apply(clean_amount)
    )

    df["declared_avg_ticket_size"] = (
        pd.to_numeric(
            df["declared_avg_ticket_size"],
            errors="coerce",
        )
    )

    df["merchant_status"] = (
        df["merchant_status"]
        .apply(
            lambda x: normalize_status(
                x,
                MERCHANT_STATUS_MAP,
            )
        )
    )

    # --------------------------------------------------------
    # Data-quality flags
    # --------------------------------------------------------

    df["ticket_size_negative_flag"] = (
        df["declared_avg_ticket_size"] < 0
    ).astype(int)

    df["ticket_size_missing_flag"] = (
        df["declared_avg_ticket_size"].isna()
    ).astype(int)

    df["mcc_missing_flag"] = (
        df["mcc"].isna()
    ).astype(int)

    df["settlement_account_missing_flag"] = (
        df["settlement_account"].isna()
    ).astype(int)

    df["onboarding_date_missing_flag"] = (
        df["onboarding_date"].isna()
    ).astype(int)

    df["merchant_suspended_flag"] = (
        df["merchant_status"] == "SUSPENDED"
    ).astype(int)

    df["merchant_blocked_flag"] = (
        df["merchant_status"] == "BLOCKED"
    ).astype(int)

    # Remove exact duplicates.
    df = df.drop_duplicates().reset_index(
        drop=True
    )

    output_path = (
        PROCESSED_DIR /
        "merchants_clean.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return {
        "dataset": "merchants",
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "exact_duplicates_removed": exact_duplicates,
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
            df["declared_avg_ticket_size"].isna().sum()
        ),
        "negative_declared_avg_ticket_size": int(
            (
                df["declared_avg_ticket_size"] < 0
            ).sum()
        ),
    }


# ============================================================
# CHARGEBACKS
# ============================================================

def clean_chargebacks():

    df = load_json(
        RAW_DIR / "track1_chargebacks.json"
    )

    raw_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())

    for column in [
        "complaint_id",
        "txn_id",
        "user_id",
    ]:
        df[f"{column}_raw"] = df[column]

        df[column] = df[column].apply(
            normalize_id
        )

    # Merchant ID canonicalization.
    df["merchant_id_raw"] = df["merchant_id"]

    df["merchant_id"] = df["merchant_id"].apply(
        lambda x: normalize_id(
            x,
            remove_hyphen=True,
        )
    )

    for column in [
        "transaction_timestamp",
        "reported_timestamp",
        "bank_response_timestamp",
    ]:
        df[column] = clean_timestamp(
            df[column]
        )

    df["disputed_amount"] = (
        df["disputed_amount"]
        .apply(clean_amount)
    )

    df["disputed_amount"] = pd.to_numeric(
        df["disputed_amount"],
        errors="coerce",
    )

    for column in [
        "reason_code",
        "complaint_text",
        "resolution_status",
        "channel",
    ]:
        df[column] = df[column].apply(
            clean_text
        )

    df["severity"] = df["severity"].apply(
        lambda x: normalize_status(
            x,
            SEVERITY_MAP,
        )
    )

    # --------------------------------------------------------
    # Data-quality flags
    # --------------------------------------------------------

    df["disputed_amount_negative_flag"] = (
        df["disputed_amount"] < 0
    ).astype(int)

    df["disputed_amount_missing_flag"] = (
        df["disputed_amount"].isna()
    ).astype(int)

    df["txn_id_missing_flag"] = (
        df["txn_id"].isna()
    ).astype(int)

    df["transaction_timestamp_missing_flag"] = (
        df["transaction_timestamp"].isna()
    ).astype(int)

    df["reported_timestamp_missing_flag"] = (
        df["reported_timestamp"].isna()
    ).astype(int)

    df["bank_response_timestamp_missing_flag"] = (
        df["bank_response_timestamp"].isna()
    ).astype(int)

    df["critical_flag"] = (
        df["severity"] == "CRITICAL"
    ).astype(int)

    df["high_flag"] = (
        df["severity"] == "HIGH"
    ).astype(int)

    # Remove exact duplicates.
    df = df.drop_duplicates().reset_index(
        drop=True
    )

    output_path = (
        PROCESSED_DIR /
        "chargebacks_clean.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return {
        "dataset": "chargebacks",
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "exact_duplicates_removed": exact_duplicates,
        "missing_complaint_id": int(
            df["complaint_id"].isna().sum()
        ),
        "missing_txn_id": int(
            df["txn_id"].isna().sum()
        ),
        "missing_disputed_amount": int(
            df["disputed_amount"].isna().sum()
        ),
        "negative_disputed_amount": int(
            (df["disputed_amount"] < 0).sum()
        ),
        "missing_transaction_timestamp": int(
            df["transaction_timestamp"].isna().sum()
        ),
        "missing_reported_timestamp": int(
            df["reported_timestamp"].isna().sum()
        ),
        "missing_bank_response_timestamp": int(
            df["bank_response_timestamp"].isna().sum()
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("UPI SENTINEL — DATA RESCUE PIPELINE")
    print("=" * 60)

    print("\n[1/4] Cleaning UPI transactions...")
    transactions = clean_transactions()

    print("[2/4] Cleaning KYC records...")
    kyc = clean_kyc()

    print("[3/4] Cleaning merchant master...")
    merchants = clean_merchants()

    print("[4/4] Cleaning chargebacks...")
    chargebacks = clean_chargebacks()

    report = [
        transactions,
        kyc,
        merchants,
        chargebacks,
    ]

    report_path = (
        REPORT_DIR /
        "cleaning_report.json"
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

    print("\n" + "=" * 60)
    print("DATA RESCUE COMPLETE")
    print("=" * 60)

    for item in report:
        print(
            f"{item['dataset']}: "
            f"{item['raw_rows']:,} → "
            f"{item['clean_rows']:,} rows"
        )

    print(
        f"\nCleaning report: {report_path}"
    )

    print(
        f"Processed data: {PROCESSED_DIR}"
    )


if __name__ == "__main__":
    main()