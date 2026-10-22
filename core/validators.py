import pandas as pd
from core.config import MIN_DURATION_MINUTES, MAX_DURATION_HOURS

def clean_and_validate_logs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw ERP/MES logs by filtering out anomalies, invalid dates, zero quantities, and extreme outliers.
    """
    cleaned_df = df.copy()

    # Convert timestamp columns to datetime objects
    cleaned_df['czas_start'] = pd.to_datetime(cleaned_df['czas_start'], errors='coerce')
    cleaned_df['czas_stop'] = pd.to_datetime(cleaned_df['czas_stop'], errors='coerce')

    # Drop rows with unparseable timestamps
    cleaned_df = cleaned_df.dropna(subset=['czas_start', 'czas_stop'])

    # Calculate actual execution duration in minutes
    cleaned_df['duration_minutes'] = (cleaned_df['czas_stop'] - cleaned_df['czas_start']).dt.total_seconds() / 60.0

    # Data hygiene mask: valid duration range and positive product quantities
    max_duration_minutes = MAX_DURATION_HOURS * 60.0
    valid_mask = (
        (cleaned_df['duration_minutes'] >= MIN_DURATION_MINUTES) & 
        (cleaned_df['duration_minutes'] <= max_duration_minutes) & 
        (cleaned_df['ilosc'] > 0)
    )

    return cleaned_df[valid_mask].copy()