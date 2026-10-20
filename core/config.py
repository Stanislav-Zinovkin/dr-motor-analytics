
#Schema mapping
# Left - keys, Right - name collumns from ERP/MES

COLUMN_MAPPING = {
    "task_id": "id_operacij",
    "user_id": "id_pracownika", # login_pracownika
    "sku": "sku", # towar
    "quantity": "ilosc",
    "time_start": "czas_start",
    "time_stop": "czas_stop",
    "action_type": "typ_operacij",
    "location": "lokalizacija",
    "order_id": "id_zlecenia", # kod Zp
}

#Default types for analytics
DEFAULT_PAUSE_TYPES = ["Pauza", "Montaz", "Konfekcja"]
