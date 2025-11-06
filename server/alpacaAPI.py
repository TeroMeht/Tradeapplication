import requests
import logging

logger = logging.getLogger(__name__)

from helpers.handle_alpaca_order import handle_orders_data




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



def process_open_orders(ib, project_config):
    """Fetch open Alpaca orders, enrich with prices, and calculate position sizes."""
    
    open_orders = get_open_orders(project_config)
    if not open_orders:
        logger.info("No open orders to process. Skipping further handling.")
        return []

    # Process and enrich orders
    processed_orders = handle_orders_data(open_orders, ib, project_config)

    return processed_orders


