import sys
from pathlib import Path

# Allow running from the scripts/ folder: add the project root to the import path.
ROOT = Path(__file__).resolve().parent
if not (ROOT / "core").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from core.validators import clean_and_validate_logs, CLEANING_REPORT_LABELS

df = pd.read_csv(ROOT / "data" / "raw" / "erp_export_mock.csv")
clean, rep = clean_and_validate_logs(df, return_report=True)
for key, value in rep.items():
    print(f"{CLEANING_REPORT_LABELS.get(key, key):50} {value}")