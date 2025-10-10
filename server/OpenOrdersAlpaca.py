import requests
import pandas as pd
import math
from IBasync import get_last_ask_price
from Calculate import calculate_position_size
import requests

# --- Build Alpaca API headers ---
def build_alpaca_headers(config: dict) -> dict:
    """Construct headers required for Alpaca API requests."""
    return {
        "APCA-API-KEY-ID": config["API_Config"]["API_KEY"],
        "APCA-API-SECRET-KEY": config["API_Config"]["API_SECRET"]
    }

# --- Fetch orders from Alpaca ---
def fetch_alpaca_orders(base_url: str, headers: dict) -> list | None:
    """Fetch open orders from the Alpaca API."""
    endpoint = f"{base_url}/orders"
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching orders: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An exception occurred while fetching orders: {e}")
        return None

# --- Log orders for debugging ---
def log_alpaca_orders(orders: list) -> None:
    """Print symbol, limit price, and stop price for each Alpaca order."""
    if not orders:
        print("No open Alpaca orders.")
        return

    for i, order in enumerate(orders, start=1):
        symbol = order.get("symbol")
        limit_price = order.get("limit_price")
        stop_price = order.get("stop_price")
        print(f"Order #{i}: Symbol={symbol}, Limit Price={limit_price}, Stop Price={stop_price}")

# --- Main function to get open orders ---
def get_open_orders(config: dict) -> list | None:
    """Fetches and logs open orders from Alpaca Trading API."""
    base_url = config["API_Config"]["BASE_URL"]
    headers = build_alpaca_headers(config)
    
    orders = fetch_alpaca_orders(base_url, headers)
    
    if orders:
        log_alpaca_orders(orders)
    
    return orders

def sanitize_numeric(value) -> float | None:
    """Convert value to float, return None if NaN or invalid."""
    try:
        if value is None:
            return None
        fval = float(value)
        if math.isnan(fval):
            return None
        return fval
    except (ValueError, TypeError):
        return None

def handle_orders_data(open_orders, ib):
    """Processes open orders and returns a pandas DataFrame with calculated values."""
    data = []

    if not open_orders:
        return pd.DataFrame()  # Early exit if no orders

    for order in open_orders:
        try:
            symbol = order.get("symbol")
            if not symbol:
                continue  # skip invalid order

            # Convert prices safely
            limit_price = sanitize_numeric(order.get("limit_price")) or 0.0
            stop_price = sanitize_numeric(order.get("stop_price")) or 0.0

            # Get latest price safely
            latest_price = sanitize_numeric(get_last_ask_price(ib, symbol)) or 0.0

            # Append row
            row = {
                "symbol": symbol,
                "limit_price": limit_price,
                "stop_price": stop_price,
                "latest_price": latest_price
            }

            # Replace any NaN with None for JSON safety
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    row[k] = None

            data.append(row)

        except Exception as e:
            print(f"Error processing order {order.get('symbol')}: {e}")
            continue

    return pd.DataFrame(data)

def define_positionsize(df: pd.DataFrame, project_config: dict) -> pd.DataFrame:
    """Calculate position size for each order in the DataFrame."""


    position_sizes = []
    for _, row in df.iterrows():
        entry_price = row.get("latest_price")
        # Use stop_price if >0, otherwise limit_price
        stop_or_limit = row.get("stop_price") or row.get("limit_price") or 0.0
        pos_size = calculate_position_size(entry_price, stop_or_limit, project_config["Risk"])


        position_sizes.append(pos_size)

    df["position_size"] = position_sizes
    return df
 
# Main function
def process_open_orders(ib, project_config):
    """Fetch open orders, calculate prices, risk, and position sizes."""
    open_orders = get_open_orders(project_config)
    df = handle_orders_data(open_orders, ib)
    df = define_positionsize(df, project_config)  # update df in place
    return df


