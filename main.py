import os
from core.metrics import load_data, get_or_update_sku_norms, calculate_worker_performance

def main():
    data_path = "data/raw/erp_export_mock.csv"
    
    if not os.path.exists(data_path):
        print(f"[Помилка] Файл не знайдено: {data_path}")
        return

    print("1. Завантаження поточних логів...")
    df = load_data(data_path)

    print("\n2. Отримання норм SKU (із кешу або перерахунок)...")
    # Передаємо force_recalculate=False для використання кешу, 
    # або True, якщо хочемо примусово оновити тижневу норму
    norms = get_or_update_sku_norms(df, force_recalculate=False)
    print(norms[['sku', 'median_seconds_per_unit']].head(5).to_string(index=False))

    print("\n3. Оцінка продуктивності працівників...")
    worker_stats = calculate_worker_performance(df, norms)
    print(worker_stats)

if __name__ == "__main__":
    main()