import os
import pandas as pd
import numpy as np
from core.config import NORMS_CACHE_PATH, FALLBACK_NORM_MINUTES

def calculate_sku_norms(df_history: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates median execution time per unit (SKU) based on cleaned historical data.
    
    TODO (Production Scaling): 
    When transitioning to a high-load MES/ERP environment with millions of rows, 
    move this aggregation entirely to the SQL database level (GROUP BY sku) 
    instead of loading raw history into Pandas in-memory dataframe to prevent OOM errors.
    """
    if df_history.empty:
        return pd.DataFrame(columns=['sku', 'median_minutes_per_unit', 'median_seconds_per_unit'])

    # Defensive validation: Prevent division by zero or negative quantities (ilosc <= 0)
    valid_mask = df_history['ilosc'] > 0
    df_clean = df_history[valid_mask].copy()

    df_clean['time_per_unit'] = df_clean['duration_minutes'] / df_clean['ilosc']

    norms = df_clean.groupby('sku')['time_per_unit'].median().reset_index()
    norms = norms.rename(columns={'time_per_unit': 'median_minutes_per_unit'})
    
    # Add human-readable unit norm in seconds
    norms['median_seconds_per_unit'] = (norms['median_minutes_per_unit'] * 60).round(1)

    return norms

def get_or_update_sku_norms(df_history: pd.DataFrame, force_recalculate: bool = False) -> pd.DataFrame:
    """
    Retrieves SKU norms from local CSV cache or recalculates them if the cache is missing/outdated.
    
    TODO (Concurrency & Race Conditions): 
    Currently uses a local CSV file cache. In a multi-worker production setup 
    (e.g., Gunicorn/Uvicorn multi-process or Celery workers), concurrent reads/writes 
    will cause file corruption ('EmptyDataError' or malformed CSV). 
    Refactor this to use Redis distributed locks or store norms inside PostgreSQL 
    with transactional updates and atomic file replacement (os.replace).
    """
    os.makedirs(os.path.dirname(NORMS_CACHE_PATH), exist_ok=True)
    file_is_valid = os.path.exists(NORMS_CACHE_PATH) and os.path.getsize(NORMS_CACHE_PATH) > 0

    norms = None
    if not force_recalculate and file_is_valid:
        try:
            norms = pd.read_csv(NORMS_CACHE_PATH)
            if norms.empty or 'median_seconds_per_unit' not in norms.columns:
                file_is_valid = False
        except Exception:
            file_is_valid = False

    if force_recalculate or not file_is_valid:
        norms = calculate_sku_norms(df_history)
        
        # TODO (Atomic Writes): Use a temporary file and os.replace() to prevent 
        # reading a partially written CSV file by another concurrent process.
        norms.to_csv(NORMS_CACHE_PATH, index=False)

    return norms

def calculate_worker_performance(df: pd.DataFrame, norms: pd.DataFrame) -> pd.DataFrame:
    """
    Computes individual worker KPIs by matching actual operational time against historical SKU medians.
    Handles unindexed/new SKUs gracefully using fallback default values.
    
    TODO (Schema Enforcement): 
    Ensure upstream ETL guarantees numeric data types for 'ilosc' and 'duration_minutes'. 
    If data comes as strings from raw ERP exports, apply pd.to_numeric(..., errors='coerce') 
    before performing arithmetic operations to avoid TypeError exceptions.
    """
    if df.empty:
        return pd.DataFrame(columns=['id_pracownika', 'total_tasks', 'total_items', 'avg_kpi'])

    merged = df.merge(norms, on="sku", how="left")

    # Fallback protection for new SKUs without historical norms
    merged['median_minutes_per_unit'] = merged['median_minutes_per_unit'].fillna(FALLBACK_NORM_MINUTES)
    
    if 'median_seconds_per_unit' in merged.columns:
        merged['median_seconds_per_unit'] = merged['median_seconds_per_unit'].fillna(FALLBACK_NORM_MINUTES * 60)

    # Compute expected duration
    merged['expected_duration'] = merged['ilosc'] * merged['median_minutes_per_unit']
    
    # Defensive math: If duration_minutes <= 0, map to NaN so pandas .mean() ignores it 
    # and prevents generating np.inf or mathematical anomalies.
    valid_duration = merged['duration_minutes'] > 0
    merged['performance_kpi'] = np.where(
        valid_duration,
        (merged['expected_duration'] / merged['duration_minutes']) * 100.0,
        np.nan
    )

    # Aggregate metrics per worker
    # Note: 'id_operacij' explicitly matches COLUMN_MAPPING definition from config
    worker_stats = merged.groupby('id_pracownika').agg(
        total_tasks=('id_oper', 'count'),
        total_items=('ilosc', 'sum'),
        avg_kpi=('performance_kpi', 'mean')
    ).reset_index()

    worker_stats['avg_kpi'] = worker_stats['avg_kpi'].round(1)

    return worker_stats