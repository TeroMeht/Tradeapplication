import logging
import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)


# Laskee positio koon kun tiedetään nämä
def calculate_position_size(entry_price, stop_price, risk):

    try:
        risk_per_unit = entry_price - stop_price
        if risk_per_unit == 0:
            raise ValueError("Entry price and stop price cannot be the same.")
        
        position_size = abs(int(risk / risk_per_unit))  # force integer
        return position_size
    
    except Exception as e:
        logger.error("Error calculating position size:", e)
        return None
    


def calculate_avg_volume_model(day5_history_datas: pd.DataFrame)-> pd.DataFrame:
    """
    Combine 5 days of intraday data and calculate the average volume
    for each Symbol-Time combination.

    Parameters
    ----------
    day5_history_datas : list[pd.DataFrame]
        List of 5 daily DataFrames with columns:
        ['Symbol', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']

    Returns
    -------
    pd.DataFrame
        A single DataFrame (average day model) with columns:
        ['Symbol', 'Time', 'Avg_volume']
    """
    # Combine all 5 days
    all_data = pd.concat(day5_history_datas, ignore_index=True)

    # Group by Symbol and Time, compute mean volume
    avg_volume_df = (
        all_data.groupby(['Symbol', 'Time'], as_index=False)['Volume']
        .mean()
        .rename(columns={'Volume': 'Avg_volume'})
    )

    return avg_volume_df

def calculate_rvol(df: pd.DataFrame) -> pd.DataFrame:

    # Check required columns
    required_cols = ['Volume', 'Avg_volume']
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")

    # cumulative sums
    df['CumVolume'] = df['Volume'].cumsum()
    df['CumAvgVolume'] = df['Avg_volume'].cumsum()

    # Rvol = cumulative volume / cumulative avg volume
    df['Rvol'] = np.where(
        (df['CumAvgVolume'] == 0) | df['CumAvgVolume'].isna(),
        0.0,
        df['CumVolume'] / df['CumAvgVolume']
    )
        # Round Rvol to 2 decimal places
    df['Rvol'] = df['Rvol'].round(2)

    return df    