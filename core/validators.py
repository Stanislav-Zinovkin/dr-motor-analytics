import unicodedata
import pandas as pd

from core.config import (
    DATETIME_FORMAT,
    MAX_DURATION_HOURS,
    MIN_DURATION_MINUTES,
    NORM_OPERATION_TYPES,
    OPERATION_TYPE_COLUMN,
)

KEY_COLUMNS = ("sku", "id_pracownika")

CLEANING_REPORT_LABELS = {
    "input_rows": "Rows in the export",
    "duplicates": "Duplicate rows",
    "other_operation_types": "Other operation types (not part of the norms)",
    "missing_keys": "Missing SKU or worker ID",
    "bad_timestamp": "Unreadable start/stop time",
    "bad_quantity": "Quantity missing or not positive",
    "too_short_or_negative": "Duration too short or negative",
    "too_long": "Duration too long (likely forgotten Stop)",
    "kept_rows": "Rows used for the analysis",
}


def _normalize_text(series: pd.Series) -> pd.Series:
    """Lower-case, strip spaces and remove diacritics: 'Montaż ' -> 'montaz'."""
    s = series.astype(str).str.strip().str.casefold().str.replace("ł", "l", regex=False)
    return s.map(
        lambda x: "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c))
    )


def _parse_datetime(series: pd.Series) -> pd.Series:
    """
    Parses timestamps. If DATETIME_FORMAT is explicitly defined in config, uses it.
    Otherwise, or if mixed formats are possible, falls back to flexible parsing.
    """
    if DATETIME_FORMAT:
        parsed = pd.to_datetime(series, format=DATETIME_FORMAT, errors="coerce")
        mask_failed = parsed.isna() & series.notna() & (series.astype(str).str.strip() != "")
        if mask_failed.any():
            parsed.loc[mask_failed] = pd.to_datetime(series[mask_failed], format="mixed", dayfirst=True, errors="coerce")
        return parsed
    
    return pd.to_datetime(series, format="mixed", dayfirst=True, errors="coerce")


def clean_and_validate_logs(df: pd.DataFrame, return_report: bool = False):
    """
    Cleans raw ERP/MES logs and keeps only rows the norms can be built from.

    Steps run in a fixed order and each row is counted under the FIRST reason
    that removes it, so the report adds up exactly:
    input_rows - (all removed counts) = kept_rows.

    Returns the cleaned DataFrame. With return_report=True
    returns (DataFrame, report_dict); see CLEANING_REPORT_LABELS for the keys.
    """
    d = df.reset_index(drop=True).copy()
    report = {"input_rows": len(d)}

    def keep_only(mask: pd.Series, key: str) -> None:
        nonlocal d
        report[key] = int((~mask).sum())
        d = d[mask].reset_index(drop=True)

    # 1. Exact duplicates (the same operation exported twice)
    subset = ["id_oper"] if "id_oper" in d.columns else None
    keep_only(~d.duplicated(subset=subset), "duplicates")

    # 2. Only the operation types the norms are built for
    can_filter = OPERATION_TYPE_COLUMN in d.columns
    if NORM_OPERATION_TYPES and can_filter:
        allowed = set(_normalize_text(pd.Series(NORM_OPERATION_TYPES)))
        keep_only(_normalize_text(d[OPERATION_TYPE_COLUMN]).isin(allowed), "other_operation_types")
    else:
        report["other_operation_types"] = 0
    report["operation_filter_skipped"] = bool(NORM_OPERATION_TYPES) and not can_filter

    # 3. Keys: strip spaces, drop rows without SKU or worker ID
    missing = pd.Series(False, index=d.index)
    for col in KEY_COLUMNS:
        text = d[col].astype(str).str.strip()
        missing |= d[col].isna() | (text == "")
        d[col] = text
    keep_only(~missing, "missing_keys")

    # 4. Timestamps
    d["czas_start"] = _parse_datetime(d["czas_start"])
    d["czas_stop"] = _parse_datetime(d["czas_stop"])
    keep_only(d["czas_start"].notna() & d["czas_stop"].notna(), "bad_timestamp")

    # 5. Quantity (text like "N/A" becomes NaN and is dropped here)
    d["ilosc"] = pd.to_numeric(d["ilosc"], errors="coerce")
    keep_only(d["ilosc"] > 0, "bad_quantity")

    # 6. Duration in minutes
    d["duration_minutes"] = (d["czas_stop"] - d["czas_start"]).dt.total_seconds() / 60.0
    keep_only(d["duration_minutes"] >= MIN_DURATION_MINUTES, "too_short_or_negative")
    keep_only(d["duration_minutes"] <= MAX_DURATION_HOURS * 60.0, "too_long")

    report["kept_rows"] = len(d)
    return (d, report) if return_report else d