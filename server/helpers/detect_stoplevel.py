import logging
from decimal import Decimal
from database.db_functions import fetch_last_n_rows

logger = logging.getLogger(__name__)

def detect_stoplevel(database_config, table_name, n):
    """
    Fetch the last 'n' rows from a given table and calculate the stop level
    as 0.02 cents below the lowest value in the 'Low' column.
    
    :param database_config: Database configuration for connecting to the DB.
    :param table_name: The name of the table to query.
    :param n: The number of rows to fetch (default is 10).
    :return: The calculated stop level or None if an error occurs.
    """
    try:
        # Fetch the last 'n' rows from the table
        rows = fetch_last_n_rows(database_config, table_name, n)
        
        if rows is None or len(rows) == 0:
            logger.error(f"No rows returned from table {table_name}")
            return None
        
        # Extract the 'Low' column values (or adjust this if your table uses another column name)
        # Assuming the 'Low' column exists and is stored as a number (decimal.Decimal)
        lows = [row.get("Low") for row in rows if row.get("Low") is not None]
        
        if not lows:
            logger.error(f"No valid 'Low' values found in the last {n} rows of table {table_name}")
            return None
        
        # Find the lowest 'Low' value in the fetched rows
        lowest_low = min(lows)
        
        # Convert the subtraction constant to Decimal
        stop_level = lowest_low - Decimal('0.02')  # Subtracting 0.02 cents as Decimal

        # Log the results
        logger.info(f"Lowest 'Low' value: {lowest_low}, Stop level: {stop_level}")

        return stop_level

    except Exception as e:
        logger.error(f"Error in detect_stoplevel: {e}")
        return None

    except Exception as e:
        logger.error(f"Error in detect_stoplevel: {e}")
        return None
