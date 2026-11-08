from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Paths -------------------------------------------------------------
# Project-relative, so it works the same on Windows, in venv and in Docker (/app/...).
NORMS_CACHE_PATH = str(BASE_DIR / "data" / "processed" / "current_norms.csv")

# --- Schema mapping ----------------------------------------------------
# Left: internal key, right: column name in the ERP/MES export.
# NOTE: the right-hand names are ASSUMPTIONS until the real export headers arrive.
COLUMN_MAPPING = {
    "task_id": "id_oper",
    "user_id": "id_pracownika",
    "sku": "sku",
    "quantity": "ilosc",
    "time_start": "czas_start",
    "time_stop": "czas_stop",
    "action_type": "typ_operacji",
    "order_id": "id_zlecenia",
}

# Which column holds the operation type, and which types norms are built for.
# Matching ignores case, spaces and Polish diacritics ("Montaż" == "montaz").
# Empty list = do not filter by operation type.
OPERATION_TYPE_COLUMN = "typ_operacji"
NORM_OPERATION_TYPES = ["Konfekcja"]

# Timestamp format in the export. None = auto-detect with day-first dates.
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# --- Data hygiene ------------------------------------------------------
MIN_DURATION_MINUTES = 0.3
MAX_DURATION_HOURS = 12

# --- Norms (used by metrics.py in the next step) -----------------------
FALLBACK_NORM_MINUTES = 1.0   # temporary, replaced by "norm not defined" logic
MIN_ORDERS_PER_SKU = 20       # fewer orders -> norm is not defined
MIN_WORKERS_PER_SKU = 3       # fewer distinct workers -> norm is not defined
OUTLIER_FACTOR = 4            # order longer than 4x SKU median = likely forgotten Stop
NORMS_WINDOW_DAYS = 90        # STUB: history window for norms
NORMS_RECALC_WEEKDAY = 6      # STUB: weekly recalculation day (0=Mon ... 6=Sun)

# --- KPI zones (one source of truth for chart and table colours) -------
KPI_LOW = 90
KPI_HIGH = 110