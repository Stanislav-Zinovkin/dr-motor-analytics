import os
import random
from datetime import datetime, timedelta
import pandas as pd

def generate_mock_data(num_records=150):

    #Fake parts example
    skus = [
        "DRM0001", "DRM001SL", "DRM0002R", "DRM00122", "DRM12120", "DRM01234", " DRM02431", "DRM15505", "DRM8282KL", "DRM8872S", "DRM1407SO"
    ]

    workers = ["EMP-01", "EMP-02", "EMP-03", "EMP-04", "EMP-05"]
    action_type = ["Pick","Pick", "Pick", "Konfekcja", "Montaż", "Pauza"]

    data = []
    current_time = datetime(2026, 10, 1, 8, 0, 0) #start shift

    for i in range(1, num_records + 1):
        task_id = f"TSK-{10000 + 1}"
        worker_id = random.choice(workers)
        sku = random.choice(skus)
        quantity = random.randint(1, 15)
        action_type = random.choice(action_type)
        order_id = f"ORD-{5000 + (i % 40)}"

        #duration 
        if action_type == "Pauza":
            duration_minutes = random.randint(15, 45)
        elif action_type in ["Montaz", "Konfekcija"]:
            duration_minutes = random.randint(10, 30)
        else:
            #basic time - quantity + random + some anomalies
            base_time = quantity * random.uniform(1.5, 3.5)
            if random.random() < 0.05: #5% anomalies
                base_time *= random.uniform(3.0, 5.0)
            duration_minutes = max(1, int(base_time))

        time_start = current_time
        time_stop  = time_start + timedelta(minutes=duration_minutes)

        #Next operation start with 1-5 min

        current_time = time_stop + timedelta(minutes=random.randint(1, 5))

        data.append({
            "id_operacji": task_id,
            "id_pracownika": worker_id,
            "sku": sku,
            "ilosc": quantity,
            "czas_start": time_start.strftime("%Y-%m-%d %H:%M:%S"),
            "czas_stop": time_stop.strftime("%Y-%m-%d %H:%M:%S"),
            "typ_operacji": action_type,
            "id_zlecenia": order_id
        })              

    df = pd.DataFrame(data)

    #Saving in dir data/

    os.makedirs("data", exist_ok=True)
    file_path = "data/erp_export_mock.csv"
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"Success! Testing file have been generated: {file_path} ({num_records} strings)")

if __name__ == "__main__":
    generate_mock_data(200)    