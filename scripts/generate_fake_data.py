import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "erp_export_mock.csv"
FMT = "%Y-%m-%d %H:%M:%S"


def generate_mock_data(start="2026-09-01", days=60, n_workers=45, n_skus=100,
                       dirty=True, seed=42) -> pd.DataFrame:
    rng = random.Random(seed)

    skus = [f"DRM{n}" for n in rng.sample(range(10000, 100000), n_skus)]
    sku_norm = {s: rng.uniform(1.0, 6.0) for s in skus}  # "справжня" норма, хв/од.
    speed = {f"EMP-{i:02d}": min(max(rng.gauss(1.0, 0.15), 0.6), 1.5)
             for i in range(1, n_workers + 1)}  # >1 = швидший за середнього

    rows, task_no = [], 10000

    def add(emp, op, sku, qty, t, minutes):
        nonlocal task_no
        task_no += 1
        rows.append({
            "id_oper": f"TSK-{task_no}", "id_pracownika": emp, "sku": sku, "ilosc": qty,
            "czas_start": t.strftime(FMT),
            "czas_stop": (t + timedelta(minutes=minutes)).strftime(FMT),
            "typ_operacji": op, "id_zlecenia": f"ORD-{5000 + task_no % 500}",
        })
        return t + timedelta(minutes=minutes + rng.randint(0, 3))

    first_day = datetime.fromisoformat(start)
    for d in range(days):
        day = first_day + timedelta(days=d)
        if day.weekday() >= 5:  # без вихідних
            continue
        for emp, k in speed.items():
            t = day.replace(hour=8, minute=0)
            end = day.replace(hour=16, minute=0)
            lunch_done = False
            while t < end:
                if not lunch_done and t.hour >= 12:
                    t = add(emp, "Pauza", "", 0, t, 30)
                    lunch_done = True
                    continue
                op = rng.choices(["Konfekcja", "Montaż"], weights=[94, 6])[0]
                sku = rng.choice(skus)
                qty = rng.randint(1, 15)
                if op == "Konfekcja":
                    minutes = qty * sku_norm[sku] / k * rng.lognormvariate(0, 0.2)
                    if rng.random() < 0.05:  # 5% збоїв/затримок
                        minutes *= rng.uniform(3, 5)
                else:
                    minutes = rng.uniform(10, 30)
                t = add(emp, op, sku, qty, t, round(max(minutes, 0.5), 1))

    df = pd.DataFrame(rows)

    if dirty:
        def pick(frac):
            return df.sample(frac=frac, random_state=rng.randint(0, 10**6)).index

        df.loc[pick(0.01), "czas_stop"] = "brak"
        df.loc[pick(0.01), "ilosc"] = 0
        swap = pick(0.005)
        df.loc[swap, ["czas_start", "czas_stop"]] = df.loc[swap, ["czas_stop", "czas_start"]].values
        df.loc[pick(0.01), "sku"] = df["sku"] + " "
        df = pd.concat([df, df.sample(frac=0.005, random_state=1)], ignore_index=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"[OK] {OUT_PATH}: {len(df)} рядків, {n_workers} працівників, {n_skus} SKU")
    return df


if __name__ == "__main__":
    generate_mock_data()