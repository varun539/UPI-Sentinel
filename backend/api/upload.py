from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(tags=["Data Rescue"])

# Maximum upload size for the demo API: 25 MB.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

SOURCE_ALIASES = {
    "transactions": "transactions",
    "transaction": "transactions",
    "upi": "transactions",
    "upi_transactions": "transactions",
    "kyc": "kyc",
    "kyc_records": "kyc",
    "merchants": "merchants",
    "merchant": "merchants",
    "merchant_master": "merchants",
    "chargebacks": "chargebacks",
    "chargeback": "chargebacks",
}

# These are intentionally minimum identity columns.
# The upload API should profile the complete file rather than reject
# legitimate files just because an optional field is absent.
EXPECTED_COLUMNS = {
    "transactions": {
        "txn_id",
        "user_id",
        "merchant_id",
        "amount",
        "status",
    },
    "kyc": {
        "user_id",
    },
    "merchants": {
        "merchant_id",
    },
    "chargebacks": {
        "complaint_id",
    },
}


def canonical_source(source_type: str) -> str:
    key = str(source_type or "").strip().lower()
    return SOURCE_ALIASES.get(key, key)


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names for inspection without changing uploaded data on disk."""
    renamed = {}
    for column in df.columns:
        cleaned = str(column).strip().lower()
        cleaned = cleaned.replace(" ", "_").replace("-", "_")
        renamed[column] = cleaned
    return df.rename(columns=renamed)


async def read_upload_to_dataframe(upload: UploadFile) -> tuple[pd.DataFrame, int]:
    filename = upload.filename or "uploaded_file"
    suffix = Path(filename).suffix.lower()

    if suffix not in {".csv", ".json"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a CSV or JSON file.",
        )

    content = await upload.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum upload size is 25 MB.",
        )

    try:
        if suffix == ".csv":
            from io import BytesIO

            df = pd.read_csv(BytesIO(content))
        else:
            payload = json.loads(content.decode("utf-8"))

            if isinstance(payload, list):
                df = pd.DataFrame(payload)
            elif isinstance(payload, dict):
                # Support common JSON dataset shapes:
                # {"data": [...]}, {"items": [...]}, {"records": [...]}
                records = None
                for key in ("data", "items", "records", "transactions", "chargebacks"):
                    if isinstance(payload.get(key), list):
                        records = payload[key]
                        break

                if records is None:
                    # A single JSON object can still represent one record.
                    df = pd.DataFrame([payload])
                else:
                    df = pd.DataFrame(records)
            else:
                raise ValueError("JSON must contain an object or array of records.")

    except pd.errors.EmptyDataError as exc:
        raise HTTPException(status_code=400, detail="CSV contains no data.") from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not decode the file as UTF-8.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse uploaded {suffix[1:].upper()} file: {exc}",
        ) from exc

    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded dataset has no rows.")

    return normalise_columns(df), len(content)


def missing_value_report(df: pd.DataFrame) -> dict[str, int]:
    result: dict[str, int] = {}

    for column in df.columns:
        count = int(df[column].isna().sum())
        if count:
            result[str(column)] = count

    return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))


def duplicate_report(df: pd.DataFrame) -> dict[str, Any]:
    exact_duplicates = int(df.duplicated().sum())

    # Useful identifier duplicate counts when an ID column exists.
    id_duplicates: dict[str, int] = {}
    for column in (
        "txn_id",
        "user_id",
        "merchant_id",
        "complaint_id",
        "utr",
    ):
        if column in df.columns:
            duplicated = int(df[column].dropna().duplicated().sum())
            if duplicated:
                id_duplicates[column] = duplicated

    return {
        "exact_duplicate_rows": exact_duplicates,
        "duplicate_identifier_values": id_duplicates,
    }


def schema_report(source: str, columns: list[str]) -> dict[str, Any]:
    expected = EXPECTED_COLUMNS.get(source, set())
    actual = set(columns)

    missing_required = sorted(expected - actual)
    matched_required = sorted(expected & actual)

    return {
        "expected_minimum_columns": sorted(expected),
        "matched_required_columns": matched_required,
        "missing_required_columns": missing_required,
        "status": "VALID" if not missing_required else "REVIEW",
    }


def data_quality_score(
    row_count: int,
    missing_count: int,
    duplicate_count: int,
) -> int:
    """
    A simple data-quality indicator for the upload preview.
    It is deliberately presented as a quality indicator, not an ML score.
    """
    if row_count <= 0:
        return 0

    missing_ratio = min(missing_count / max(row_count, 1), 1.0)
    duplicate_ratio = min(duplicate_count / max(row_count, 1), 1.0)

    score = 100 - (missing_ratio * 60) - (duplicate_ratio * 40)
    return max(0, min(100, round(score)))


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    source_type: str = Form(...),
):
    """
    Stage 1 Data Rescue endpoint.

    Receives one CSV/JSON dataset, profiles it in memory, validates its
    minimum identity schema, and returns a data-quality report.

    IMPORTANT:
    - The uploaded file is NOT written into data/raw or data/processed.
    - Existing hackathon data is never overwritten.
    - Full pipeline execution is intentionally a later stage.
    """
    source = canonical_source(source_type)

    if source not in EXPECTED_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported source type.",
                "supported_sources": [
                    "transactions",
                    "kyc",
                    "merchants",
                    "chargebacks",
                ],
            },
        )

    df, file_size = await read_upload_to_dataframe(file)

    duplicates = duplicate_report(df)
    missing = missing_value_report(df)
    schema = schema_report(source, list(df.columns))

    missing_total = int(sum(missing.values()))
    quality = data_quality_score(
        row_count=len(df),
        missing_count=missing_total,
        duplicate_count=duplicates["exact_duplicate_rows"],
    )

    return {
        "status": "validated",
        "source": source,
        "filename": file.filename or "uploaded_file",
        "file_size_bytes": file_size,
        "raw_rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(column) for column in df.columns],
        "duplicates": duplicates,
        "missing_fields": missing,
        "missing_value_count": missing_total,
        "schema": schema,
        "data_quality_score": quality,
        "next_step": (
            "ready_for_cleaning"
            if schema["status"] == "VALID"
            else "schema_review_required"
        ),
        "message": (
            f"{len(df):,} records detected. "
            f"{duplicates['exact_duplicate_rows']:,} exact duplicate rows detected. "
            "Dataset is ready for the cleaning stage."
            if schema["status"] == "VALID"
            else (
                f"{len(df):,} records detected, but required source columns "
                "need review before cleaning."
            )
        ),
    }
