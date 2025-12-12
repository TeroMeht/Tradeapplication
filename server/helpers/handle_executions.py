from datetime import datetime, timedelta
import pytz
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def is_entry_allowed(executions_df: pd.DataFrame, symbol: str, project_config: dict):
    """
    Returns (allowed: bool, message: str)

    Entry is allowed when:
      - No previous executions for this symbol, OR
      - The latest execution is older than max_entry_freq_minutes.
    """
    try:
        threshold_minutes = project_config["max_entry_freq_minutes"]

        # ---- FIX: Handle missing or empty DataFrame columns safely ----
        if executions_df is None or executions_df.empty:
            message = f"No executions found. Entry allowed for {symbol}."
            logging.info(message)
            return True, message

        # Make sure required columns exist
        if "Symbol" not in executions_df.columns or "Time" not in executions_df.columns:
            message = (
                f"Executions DataFrame missing required columns. "
                f"Entry allowed for {symbol}. (Columns present: {list(executions_df.columns)})"
            )
            logging.info(message)
            return True, message
        # -----------------------------------------------------------------

        # Filter by symbol
        symbol_execs = executions_df[executions_df["Symbol"] == symbol]

        if symbol_execs.empty:
            message = f"No previous executions for {symbol}. Entry allowed."
            logging.info(message)
            return True, message

        # Latest execution timestamp
        latest_time_str = symbol_execs["Time"].max()
        latest_time = datetime.fromisoformat(latest_time_str)

        # Current Helsinki time
        helsinki_now = datetime.now(pytz.timezone("Europe/Helsinki"))

        # Time since last execution
        elapsed = helsinki_now - latest_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)

        # Check threshold
        if elapsed <= timedelta(minutes=threshold_minutes):
            message = (
                f"Entry NOT allowed for {symbol}: last execution was "
                f"{minutes}m {seconds}s ago (limit: {threshold_minutes} minutes)"
            )
            logging.info(message)
            return False, message

        message = (
            f"Entry allowed for {symbol}: last execution was "
            f"{minutes}m {seconds}s ago (limit: {threshold_minutes} minutes)"
        )
        logging.info(message)
        return True, message

    except Exception as e:
        message = f"Error in is_entry_allowed: {e}"
        logging.error(message)
        return False, message
