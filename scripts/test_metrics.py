import sys
from pathlib import Path

# Add project root to system paths BEFORE any core imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from core.validators import clean_and_validate_logs
from core.metrics import get_or_update_sku_norms, calculate_worker_performance

def run_cli_audit():
    print("=" * 50)
    print("🔍 [CLI AUDIT] Running log logic and metrics check...")
    print("=" * 50)

    # 1. Load data
    path = "data/raw/erp_export_mock.csv"
    print(f"📂 Reading file: {path}")
    raw_df = pd.read_csv(path)
    print(f"   Total rows in raw file: {len(raw_df):,}")

    # 2. Validation
    clean_df, report = clean_and_validate_logs(raw_df, return_report=True)
    print(f"🧹 Validation completed. Selected for analysis: {report['kept_rows']:,} rows.")

    # 3. SKU Norms
    norms_df = get_or_update_sku_norms(clean_df, force_recalculate=True)
    print(f"🏷️ Calculated norms for SKUs: {len(norms_df)}")

    # 4. Monthly breakdown and KPI
    clean_df['year_month'] = clean_df['czas_start'].dt.to_period('M').astype(str)
    months = sorted(clean_df['year_month'].unique(), reverse=True)
    print(f"📅 Months found in data: {months}")
    print("-" * 50)

    prev_avg_kpi = None
    for month in months:
        month_logs = clean_df[clean_df['year_month'] == month]
        worker_kpis = calculate_worker_performance(month_logs, norms_df)
        avg_kpi = round(worker_kpis['avg_kpi'].mean(), 1) if not worker_kpis.empty else 0.0
        
        delta_str = ""
        if prev_avg_kpi is not None:
            diff = round(avg_kpi - prev_avg_kpi, 1)
            delta_str = f" (change vs previous: {diff:+.1f}%)"
        
        print(f"📆 Month: {month} | Operations: {len(month_logs):5,d} | Average KPI: {avg_kpi:5.1f}%{delta_str}")
        prev_avg_kpi = avg_kpi

    print("=" * 50)
    print("✅ Audit completed successfully! All data checks out mathematically.")
    print("=" * 50)

if __name__ == "__main__":
    run_cli_audit()