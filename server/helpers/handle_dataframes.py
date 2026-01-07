from common.calculate import *
import pandas as pd
import logging
from typing import Optional, List,Dict


# Tämä on erillinen koodikirjasto jolla käsittelen sisään tulevia bars dataa pandas dataframeiksi
logger = logging.getLogger(__name__)  # module-specific logger

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

@dataclass
class IncomingBar:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    average: Optional[float]
    barCount: Optional[int]


def incoming_bars_to_datamodel_format(bars) -> List[IncomingBar]:
    """
    Convert a list of raw IBKR bar objects into a list of IncomingBar dataclasses.
    
    Each bar must have attributes: date, open, high, low, close, volume
    Optional: average, barCount
    """
    incoming_bars = []
    
    for bar in bars:
        incoming_bars.append(
            IncomingBar(
                date=bar.date,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                average=getattr(bar, "average", None),
                barCount=getattr(bar, "barCount", None)
            )
        )

    return incoming_bars



def intraday_datapipe(bars: List[IncomingBar], time_zone:str) -> pd.DataFrame:
    """
    Convert a list of IncomingBar dataclasses to a pandas DataFrame.
    Keeps datetime as timezone-aware and capitalizes all column names.
    """

    # Convert dataclasses to DataFrame
    df = pd.DataFrame([asdict(bar) for bar in bars])

    # Drop optional columns if present
    df = df.drop(columns=[c for c in ["average", "barCount"] if c in df.columns])

    # --- Convert datetime to Helsinki timezone ---
    df["date"] = pd.to_datetime(df["date"], utc=True)  # treat all as UTC
    df["date"] = df["date"].dt.tz_convert(ZoneInfo(time_zone))  # convert to Helsinki coming from project config

    # --- Split Date / Time for readability ---
    df["Date"] = df["date"].dt.date      # keep only date part
    df["Time"] = df["date"].dt.time      # optional: separate Time column

    # Drop original 'date' column if you want
    df = df.drop(columns=["date"])

    # Capitalize all remaining column names
    df.columns = [col.capitalize() for col in df.columns]

    return df

def daily_datapipe(bars: List[IncomingBar]) -> pd.DataFrame:
    """
    Convert a list of IncomingBar dataclasses to a pandas DataFrame.
    Keeps datetime as timezone-aware and capitalizes all column names.
    """

    # Convert dataclasses to DataFrame
    df = pd.DataFrame([asdict(bar) for bar in bars])

    # Capitalize all remaining column names
    df.columns = [col.capitalize() for col in df.columns]

    return df


def handle_incoming_dataframe_intraday(bars: List[IncomingBar], symbol:str, time_zone:str)-> pd.DataFrame:
    """
    Process IBKR bars into a pandas DataFrame (or dataclasses if needed):
    - Adjust timezone
    - Calculate VWAP / EMA9
    """
    # Step 1: Convert to dataclasses
    incoming_bars = incoming_bars_to_datamodel_format(bars)

    # Step 2: Convert to DataFrame
    df = intraday_datapipe(incoming_bars,time_zone)

    # Step 4: Assign symbol
    df["Symbol"] = symbol

    # Step 5: Calculate indicators

    # --- Reorder columns ---
    desired_order = [
        "Symbol","Date", "Time","Open", "High", "Low", "Close", "Volume"
    ]
    df = df[desired_order]
    return df



def handle_incoming_dataframe_intradays_volume(bars: List[IncomingBar], symbol:str, time_zone:str)-> pd.DataFrame:

    # Step 1: Convert to dataclasses
    incoming_bars = incoming_bars_to_datamodel_format(bars)

    # Step 2: Convert to DataFrame
    df = intraday_datapipe(incoming_bars,time_zone)

    # Step 4: Assign symbol
    df["Symbol"] = symbol

    # --- Reorder columns ---
    desired_order = [
        "Symbol","Date","Time", "Open", "High", "Low", "Close", "Volume"]
    
    df = df[desired_order]
    # Step 5: Calculate average volume model
    df = calculate_avg_volume_model([df])

    return df


def handle_intraday_rvol_dataset(intraday_results: list[pd.DataFrame], avg_volume_results_5d: list[pd.DataFrame]) -> pd.DataFrame:

    rvol_datasets = {}

    for intraday_df, avg_volume_df in zip(intraday_results, avg_volume_results_5d):
        if intraday_df is None or intraday_df.empty:
            logger.warning("Empty intraday DataFrame, skipping.")
            continue
        
        symbol = intraday_df['Symbol'].iloc[0]

        # Ensure avg_volume_df has the necessary columns
        required_cols = ['Symbol', 'Time', 'Avg_volume']
        for col in required_cols:
            if col not in avg_volume_df.columns:
                logger.error(f"Avg volume DataFrame for {symbol} missing column: {col}")
                continue

        # Merge intraday with avg volume on Symbol, Date, Time
        merged_df = pd.merge(
            intraday_df,
            avg_volume_df[required_cols],
            on=['Symbol', 'Time'],
            how='left'
        )
        merged_df = calculate_rvol(merged_df)

        rvol_datasets[symbol] = merged_df
        logger.debug(f"{symbol} - last 10 rows with Rvol:\n{merged_df.tail(10)}")

    return rvol_datasets


