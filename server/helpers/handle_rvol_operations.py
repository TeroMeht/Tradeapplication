import logging
from typing import List, Dict
import pandas as pd

from ib_insync import IB, Stock

from helpers.handle_market_scan import fetch_intraday_history, fetch_intraday_volume_history
from helpers.handle_dataframes import handle_intraday_rvol_dataset

def compute_rvol_from_clean_data(ib: IB, clean_data: list, time_zone: str) -> dict:
    """
    High-level RVOL builder that uses:
        - fetch_intraday_history()  (1 day)
        - fetch_intraday_volume_history()  (5 days)
        - handle_intraday_rvol_dataset()  (merge + Rvol calc)

    Returns a dictionary indexed by symbol containing:
        {
            symbol: {
                "rvol": float,
                "current_volume": float,
                "avg_volume": float
            }
        }
    """

    intraday_results = []
    avg_volume_results = []

    for item in clean_data:
        symbol = item.get("symbol")
        if not symbol:
            continue

        try:
            # 1️⃣ Fetch TODAY intraday (Open → Now)
            intraday_df = fetch_intraday_history(ib, symbol, time_zone)

            # 2️⃣ Fetch 5-DAY intraday for avg volume model
            avg_df = fetch_intraday_volume_history(ib, symbol, time_zone)

            intraday_results.append(intraday_df)
            avg_volume_results.append(avg_df)

        except Exception as e:
            logging.error(f"RVOL data fetch failed for {symbol}: {e}")
            intraday_results.append(None)
            avg_volume_results.append(None)

    # 3️⃣ Use your pre-built merge + rvol logic
    rvol_datasets = handle_intraday_rvol_dataset(intraday_results, avg_volume_results)

    # 4️⃣ Convert DataFrame result → simple map for frontend
    rvol_map = {}

    for symbol, df in rvol_datasets.items():
        if df is None or df.empty:
            rvol_map[symbol] = {"rvol": None, "current_volume": None, "avg_volume": None}
            continue

        # Last row is "current moment"
        last_row = df.iloc[-1]

        rvol_map[symbol] = {
            "rvol": float(last_row.get("Rvol", None)),
            "current_volume": float(last_row.get("Volume", None)),
            "avg_volume": float(last_row.get("Avg_volume", None)),
        }

    return rvol_map