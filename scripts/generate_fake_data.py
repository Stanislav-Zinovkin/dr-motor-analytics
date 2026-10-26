import os
import random
from datetime import datetime, timedelta
import pandas as pd

def generate_mock_data(num_records=2000):
    """
    Generates realistic mock ERP/MES operational logs for the analytics dashboard.
    SKU format: 'DRM' followed by 5 digits (e.g., DRM12345).
    Worker pool: EMP-01 to EMP-45.
    """
    
    # Generate a rich pool of 100 unique SKUs matching the 'DRM' + 5 digits format
    skus = [f"DRM{random.randint(10000, 99999)}" for _ in range(100)]

    # Extended worker pool from EMP-01 to EMP-45
    workers = [f"EMP-{i:02d}" for i in range(1, 46)]
    
    # Action types pool for the warehouse operations
    action_types_pool = ["Pick", "Pick", "Pick", "Konfekcja", "Montaż", "Pauza"]

    data = []
    current_time = datetime(2026, 10, 1, 8, 0, 0) # Shift starting point

    for i in range(1, num_records + 1):
        task_id = f"TSK-{10000 + i}"
        worker_id = random.choice(workers)
        sku = random.choice(skus)
        quantity = random.randint(1, 15)
        curr_action = random.choice(action_types_pool)
        order_id = f"ORD-{5000 + (i % 500)}"

        # Duration calculation based on operation type
        if curr_action == "Pauza":
            duration_minutes = random.randint(15, 45)
        elif curr_action in ["Montaż", "Konfekcja"]:
            duration_minutes = random.randint(10, 30)
        else:
            # Base picking time calculation with occasional anomaly injections
            base_time = quantity * random.uniform(1.5, 3.5)
            if random.random() < 0.05: # 5% anomaly probability (delays/issues)
                base_time *= random.uniform(3.0, 5.0)
            duration_minutes = max(1, int(base_time))

        time_start = current_time
        time_stop  = time_start + timedelta(minutes=duration_minutes)

        # Next operation starts within 1-5 minutes
        current_time = time_stop + timedelta(minutes=random.randint(1, 5))

        data.append({
            "id_oper": task_id,
            "id_pracownika": worker_id,
            "sku": sku,
            "ilosc": quantity,
            "czas_start": time_start.strftime("%Y-%m-%d %H:%M:%S"),
            "czas_stop": time_stop.strftime("%Y-%m-%d %H:%M:%S"),
            "typ_operacji": curr_action,
            "id_zlecenia": order_id
        })            

    df = pd.DataFrame(data)

    # Save generated data into the data/ directory
    os.makedirs("data", exist_ok=True)
    file_path = "data/erp_export_mock.csv"
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"[SUCCESS] Mock dataset generated: {file_path} ({num_records} rows, {len(workers)} workers, {len(skus)} SKUs)")

if __name__ == "__main__":
    generate_mock_data(2000)