import requests
import logging

logger = logging.getLogger(__name__)

from helpers.handle_alpaca_order import handle_orders_data
from database.db_functions import fetch_active_open_orders



# --- Fetch orders from Alpaca ---
def fetch_alpaca_orders(base_url: str, headers: dict) -> list | None:
    """Fetch open orders from the Alpaca API."""
    endpoint = f"{base_url}/orders"
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching orders: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"An exception occurred while fetching orders: {e}")
        return None

# --- Main function to get open orders ---
def get_open_orders(project_config: dict) -> list:
    base_url = project_config["BASE_URL"]
    headers = {
        "APCA-API-KEY-ID": project_config["API_KEY"],
        "APCA-API-SECRET-KEY": project_config["API_SECRET"]
    }
    
    orders = fetch_alpaca_orders(base_url, headers)
    
    if not orders:
        logger.info("No open Alpaca orders.")
        return []
    else:
        for i, order in enumerate(orders, start=1):
            symbol = order.get("symbol")
            limit_price = order.get("limit_price")
            stop_price = order.get("stop_price")
            logger.info("Order #%d: Symbol=%s, Limit Price=%s, Stop Price=%s",
                        i, symbol, limit_price, stop_price)
    
    return orders





# Get autoorders from db
def get_auto_orders(database_config):
    """
    Fetch active auto orders from the database.
    """
    auto_orders = fetch_active_open_orders(database_config)

    if not auto_orders:
        logger.info("No active auto orders found in DB.")
        return []

    return auto_orders




def process_open_orders(ib, project_config, database_config):
    """
    Fetch open Alpaca orders and DB auto orders,
    combine them, enrich with prices, and calculate position sizes.
    """

    # --- Fetch Alpaca orders ---
    alpaca_orders = get_open_orders(project_config)

    # --- Fetch DB auto orders ---
    auto_orders = get_auto_orders(database_config)

    if not alpaca_orders and not auto_orders:
        logger.info("No Alpaca or DB orders to process. Skipping.")
        return []

    # --- Normalize DB orders to look like Alpaca orders ---
    normalized_auto_orders = []
    for order in auto_orders:
        normalized_auto_orders.append({
            "id": order["Id"],
            "symbol": order["Symbol"],
            "stop_price": order["Stop"],
            "created_at": order["Date"],
            "source": "DB"          # important for later logic
        })

    # --- Tag Alpaca orders ---
    for order in alpaca_orders:
        order["source"] = "ALPACA"

    # --- Combine both ---
    combined_orders = alpaca_orders + normalized_auto_orders

    logger.info(
        "Processing %d Alpaca orders and %d DB auto orders",
        len(alpaca_orders),
        len(normalized_auto_orders)
    )

    # --- Process and enrich orders ---
    processed_orders = handle_orders_data(
        combined_orders,
        ib,
        project_config
    )

    return processed_orders


