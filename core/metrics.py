import os
import pandas as pd

NORMS_CACHE_PATH = "data/processed/current_norms.csv"

def load_data(file_path: str) -> pd.DataFrame:
    """Завантажує фактичні логі з ERP/MES за поточний період"""
    df = pd.read_csv(file_path)

    df['czas_start'] = pd.to_datetime(df['czas_start'])
    df['czas_stop'] = pd.to_datetime(df['czas_stop'])

    df['duration_minutes'] = (df['czas_stop'] - df['czas_start']).dt.total_seconds() / 60.0

    return df

def calculate_sku_norms(df_history: pd.DataFrame) -> pd.DataFrame:
    """Чистий розрахунок медіанних норм для кожної деталі (SKU)"""
    active_df = df_history[df_history['duration_minutes'] > 0].copy()
    
    active_df['time_per_unit'] = active_df['duration_minutes'] / active_df['ilosc']

    norms = active_df.groupby('sku')['time_per_unit'].median().reset_index()
    norms = norms.rename(columns={'time_per_unit': 'median_minutes_per_unit'})
    
    # Додаємо зручний формат у секундах
    norms['median_seconds_per_unit'] = (norms['median_minutes_per_unit'] * 60).round(1)

    return norms

def get_or_update_sku_norms(df_history: pd.DataFrame, force_recalculate: bool = False) -> pd.DataFrame:
    """
    Повертає норми з кешу або перераховує їх. 
    Автоматично оновлює кеш, якщо структура полів змінилася.
    """
    os.makedirs(os.path.dirname(NORMS_CACHE_PATH), exist_ok=True)

    file_is_valid = os.path.exists(NORMS_CACHE_PATH) and os.path.getsize(NORMS_CACHE_PATH) > 0

    norms = None
    if not force_recalculate and file_is_valid:
        try:
            norms = pd.read_csv(NORMS_CACHE_PATH)
            # Перевіряємо, чи є нова колонка в кеші. Якщо немає — примусово перераховуємо, щоб оновити кеш
            if norms.empty or 'median_seconds_per_unit' not in norms.columns:
                print("[КЕШ] Структура кешу застаріла. Оновлюємо...")
                file_is_valid = False
            else:
                print(f"[КЕШ] Завантажуємо збережені тижневі норми з: {NORMS_CACHE_PATH}")
        except Exception:
            file_is_valid = False

    if force_recalculate or not file_is_valid:
        print("[ОНОВЛЕННЯ] Розраховуємо нові норми та оновлюємо кеш...")
        norms = calculate_sku_norms(df_history)
        norms.to_csv(NORMS_CACHE_PATH, index=False)
        print(f"[КЕШ] Збережено нові норми у: {NORMS_CACHE_PATH}")

    return norms

def calculate_worker_performance(df: pd.DataFrame, norms: pd.DataFrame) -> pd.DataFrame:
    """Розрахунок продуктивності працівників за фіксованими нормами"""
    merged = df.merge(norms, on="sku", how="left")

    merged['expected_duration'] = merged['ilosc'] * merged['median_minutes_per_unit']
    merged['performance_kpi'] = (merged['expected_duration'] / merged['duration_minutes']) * 100

    worker_stats = merged.groupby('id_pracownika').agg(
        total_tasks=('id_operacji', 'count'),
        total_items=('ilosc', 'sum'),
        avg_kpi=('performance_kpi', 'mean')
    ).reset_index()

    return worker_stats