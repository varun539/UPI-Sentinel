

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

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



# ============================================================================
# LIVE DATA RESCUE -> FULL INTELLIGENCE PIPELINE
# ============================================================================
#
# The existing pipeline is deliberately reused in its current stage order.
# There is no second analytics implementation here.
#
# Uploads replace ONE raw source at a time, then the complete pipeline is
# executed so every downstream table (transactions, users, merchants,
# networks, investigations and AI queries) is regenerated from the new data.
#
# Runtime uploads are intentionally local to the running service. On a Render
# restart/redeploy the repository baseline dataset returns.
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

RAW_FILENAMES = {
    "transactions": "track1_upi_transactions.csv",
    "kyc": "track1_kyc_records.csv",
    "merchants": "track1_merchants_master.csv",
    "chargebacks": "track1_chargebacks.json",
}

PIPELINE_STEPS = [
    ("01_profile.py", "Profile"),
    ("02_cleaning.py", "Cleaning"),
    ("03_validation.py", "Validation"),
    ("04_transform.py", "Transformation"),
    ("05_features.py", "Feature engineering"),
    ("06_fraud_graph.py", "Fraud graph"),
    ("07_anomaly_detection.py", "ML anomaly detection"),
    ("08_unified_intelligence.py", "Unified intelligence"),
]

# Prevent two judges/requests from rewriting data/processed simultaneously.
PIPELINE_LOCK = threading.Lock()

# In-memory job state is enough for the hackathon demo and avoids long HTTP
# request timeouts while the full pipeline runs in the background.
UPLOAD_JOBS: dict[str, dict[str, Any]] = {}
UPLOAD_JOBS_LOCK = threading.Lock()


def _set_job(job_id: str, **updates: Any) -> None:
    with UPLOAD_JOBS_LOCK:
        if job_id in UPLOAD_JOBS:
            UPLOAD_JOBS[job_id].update(updates)


def _active_pipeline_exists() -> bool:
    with UPLOAD_JOBS_LOCK:
        return any(
            job.get("status") in {"queued", "running"}
            for job in UPLOAD_JOBS.values()
        )


def _write_runtime_source(
    source: str,
    df: pd.DataFrame,
    original_filename: str,
) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / RAW_FILENAMES[source]

    # The existing pipeline expects CSV for the first three sources and JSON
    # for chargebacks. Normalize into those exact expected formats regardless
    # of whether the judge uploaded CSV or JSON.
    if source == "chargebacks":
        df.to_json(
            target,
            orient="records",
            indent=2,
            date_format="iso",
        )
    else:
        df.to_csv(target, index=False)

    return target


def _snapshot_state(source: str) -> Path:
    """
    Snapshot only the files/directories that the existing pipeline can mutate.
    This gives us a rollback path if a pipeline stage fails.
    """
    snapshot = Path(tempfile.mkdtemp(prefix="upi_sentinel_upload_"))

    raw_target = RAW_DIR / RAW_FILENAMES[source]
    if raw_target.exists():
        shutil.copy2(raw_target, snapshot / raw_target.name)

    if PROCESSED_DIR.exists():
        shutil.copytree(
            PROCESSED_DIR,
            snapshot / "processed",
            dirs_exist_ok=True,
        )

    if REPORT_DIR.exists():
        shutil.copytree(
            REPORT_DIR,
            snapshot / "reports",
            dirs_exist_ok=True,
        )

    return snapshot


def _restore_snapshot(source: str, snapshot: Path) -> None:
    raw_target = RAW_DIR / RAW_FILENAMES[source]
    old_raw = snapshot / raw_target.name

    if old_raw.exists():
        shutil.copy2(old_raw, raw_target)
    elif raw_target.exists():
        raw_target.unlink()

    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)
    processed_backup = snapshot / "processed"
    if processed_backup.exists():
        shutil.copytree(
            processed_backup,
            PROCESSED_DIR,
            dirs_exist_ok=True,
        )

    if REPORT_DIR.exists():
        shutil.rmtree(REPORT_DIR)
    reports_backup = snapshot / "reports"
    if reports_backup.exists():
        shutil.copytree(
            reports_backup,
            REPORT_DIR,
            dirs_exist_ok=True,
        )


def _clean_json(value: Any) -> Any:
    """Make pipeline reports safe for FastAPI JSON serialization."""
    if isinstance(value, dict):
        return {str(k): _clean_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean_json(v) for v in value]
    if hasattr(value, "item"):
        try:
            return _clean_json(value.item())
        except Exception:
            pass
    if isinstance(value, float):
        if pd.isna(value):
            return None
        return value
    return value


def _read_pipeline_outputs() -> dict[str, Any]:
    result: dict[str, Any] = {}

    cleaning_path = REPORT_DIR / "cleaning_report.json"
    unified_path = REPORT_DIR / "unified_intelligence_report.json"

    if cleaning_path.exists():
        try:
            with open(cleaning_path, "r", encoding="utf-8") as f:
                result["cleaning_report"] = json.load(f)
        except Exception:
            result["cleaning_report"] = []

    if unified_path.exists():
        try:
            with open(unified_path, "r", encoding="utf-8") as f:
                result["unified_report"] = json.load(f)
        except Exception:
            result["unified_report"] = {}

    return _clean_json(result)


@router.post("/upload", status_code=202)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: str = Form(...),
):
    """
    Upload one Sentinel source and run the existing full intelligence pipeline.

    Flow:
      validate -> stage raw source -> background pipeline -> poll job status

    The endpoint returns quickly with a job_id so Render/proxy request
    timeouts do not interrupt a longer ML/graph pipeline run.
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

    if _active_pipeline_exists():
        raise HTTPException(
            status_code=409,
            detail=(
                "Another intelligence pipeline run is already in progress. "
                "Please wait for it to finish before uploading another source."
            ),
        )

    df, file_size = await read_upload_to_dataframe(file)

    duplicates = duplicate_report(df)
    missing = missing_value_report(df)
    schema = schema_report(source, list(df.columns))

    if schema["status"] != "VALID":
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Required source columns are missing. "
                    "The file was not staged and existing intelligence was not changed."
                ),
                "schema": schema,
            },
        )

    missing_total = int(sum(missing.values()))
    quality = data_quality_score(
        row_count=len(df),
        missing_count=missing_total,
        duplicate_count=duplicates["exact_duplicate_rows"],
    )

    filename = file.filename or "uploaded_file"

    # Snapshot BEFORE replacing the live raw source. The background task uses
    # the snapshot for rollback if any downstream stage fails.
    with PIPELINE_LOCK:
        if _active_pipeline_exists():
            raise HTTPException(
                status_code=409,
                detail="Another intelligence pipeline run is already in progress.",
            )

        snapshot = _snapshot_state(source)
        target = _write_runtime_source(source, df, filename)

    job_id = f"upload_{int(time.time() * 1000)}_{os.urandom(4).hex()}"

    with UPLOAD_JOBS_LOCK:
        UPLOAD_JOBS[job_id] = {
            "status": "queued",
            "stage": "Queued for intelligence pipeline",
            "progress": 0,
            "source": source,
            "filename": filename,
            "raw_rows": int(len(df)),
            "file_size_bytes": file_size,
            "data_quality_score": quality,
            "duplicates": duplicates,
            "missing_fields": missing,
            "schema": schema,
            # Pass the already-created snapshot to the job so rollback is
            # performed against the state from immediately before this upload.
            "_snapshot": str(snapshot),
            "created_at": time.time(),
        }

    def run_job_with_snapshot() -> None:
        # The normal helper creates its own snapshot, so for the upload flow we
        # use a small adapter that keeps the exact pre-upload snapshot.
        saved_snapshot = Path(
            UPLOAD_JOBS.get(job_id, {}).get("_snapshot", "")
        )
        local_snapshot = saved_snapshot if saved_snapshot.exists() else None

        try:
            _set_job(
                job_id,
                status="running",
                stage="Running Sentinel intelligence pipeline",
                progress=5,
            )

            started = time.perf_counter()

            with PIPELINE_LOCK:
                for index, (script_name, label) in enumerate(PIPELINE_STEPS, start=1):
                    script = BASE_DIR / "pipeline" / script_name
                    if not script.exists():
                        raise RuntimeError(
                            f"Pipeline stage not found: pipeline/{script_name}"
                        )

                    progress = 5 + int(((index - 1) / len(PIPELINE_STEPS)) * 90)
                    _set_job(
                        job_id,
                        stage=f"{label} ({index}/{len(PIPELINE_STEPS)})",
                        progress=progress,
                    )

                    completed = subprocess.run(
                        [sys.executable, str(script)],
                        cwd=str(BASE_DIR),
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )

                    if completed.returncode != 0:
                        output = (completed.stderr or completed.stdout or "").strip()
                        raise RuntimeError(
                            f"{label} failed.\n{output[-4000:]}"
                        )

                outputs = _read_pipeline_outputs()

            cleaning_report = outputs.get("cleaning_report", [])
            source_rows = {}
            for item in cleaning_report if isinstance(cleaning_report, list) else []:
                dataset = item.get("dataset")
                if dataset == "upi_transactions":
                    source_rows["transactions"] = int(item.get("clean_rows", 0))
                elif dataset == "kyc":
                    source_rows["kyc"] = int(item.get("clean_rows", 0))
                elif dataset == "merchants":
                    source_rows["merchants"] = int(item.get("clean_rows", 0))
                elif dataset == "chargebacks":
                    source_rows["chargebacks"] = int(item.get("clean_rows", 0))

            duration = round(time.perf_counter() - started, 2)

            _set_job(
                job_id,
                status="completed",
                stage="Analysis complete",
                progress=100,
                duration_seconds=duration,
                pipeline=outputs,
                source_rows=source_rows,
                message=(
                    f"{len(df):,} records from {filename} were processed through "
                    "the full Sentinel intelligence pipeline. Dashboard "
                    "intelligence has been refreshed."
                ),
            )

        except Exception as exc:
            try:
                if local_snapshot is not None:
                    with PIPELINE_LOCK:
                        _restore_snapshot(source, local_snapshot)
            except Exception as restore_exc:
                exc = RuntimeError(
                    f"{exc} | Rollback also failed: {restore_exc}"
                )

            _set_job(
                job_id,
                status="failed",
                stage="Pipeline failed",
                progress=0,
                error=str(exc),
                message=(
                    "The uploaded source could not complete the intelligence "
                    "pipeline. Previous processed intelligence was restored."
                ),
            )
        finally:
            if local_snapshot is not None:
                shutil.rmtree(local_snapshot, ignore_errors=True)
            with UPLOAD_JOBS_LOCK:
                if job_id in UPLOAD_JOBS:
                    UPLOAD_JOBS[job_id].pop("_snapshot", None)

    # Starlette/FastAPI BackgroundTasks will run this after the 202 response.
    background_tasks.add_task(run_job_with_snapshot)

    return {
        "status": "processing",
        "job_id": job_id,
        "source": source,
        "filename": filename,
        "file_size_bytes": file_size,
        "raw_rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(column) for column in df.columns],
        "duplicates": duplicates,
        "missing_fields": missing,
        "missing_value_count": missing_total,
        "schema": schema,
        "data_quality_score": quality,
        "next_step": "pipeline_processing",
        "message": (
            f"{len(df):,} records validated. "
            "Sentinel is now running cleaning, validation, transformation, "
            "feature engineering, fraud graph, ML anomaly detection and "
            "unified intelligence."
        ),
    }


@router.get("/upload/status/{job_id}")
async def upload_status(job_id: str):
    with UPLOAD_JOBS_LOCK:
        job = UPLOAD_JOBS.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Upload job not found.")

    # Never expose the private snapshot path.
    safe_job = {
        key: value
        for key, value in job.items()
        if key != "_snapshot"
    }
    return _clean_json(safe_job)
