import requests
import pandas as pd
from ib_insync import IB
from IBasync import get_last_ask_price

# Hakee Alpacca API:n kautta tilaukset
def get_open_orders(config):

    # Accessing the API_Config section
    api_key = config["API_Config"]["API_KEY"]
    api_secret = config["API_Config"]["API_SECRET"]
    base_url = config["API_Config"]["BASE_URL"]

    """Fetches open orders from Alpaca Trading API."""
    endpoint = f"{base_url}/orders"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }

    try:
        response = requests.get(endpoint, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            orders = response.json()
            for order in orders:
                print("Alpaca Open Order: ", order["symbol"], order["limit_price"], order["stop_price"])
            return orders
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An exception occurred: {e}")
        return None

def handle_orders_data(open_orders,config,ib:IB):
    """Processes open orders and returns a pandas DataFrame with calculated values."""

    # Initialize list to hold data
    data = []

    latest_price = None

    try:

        if open_orders is not None:
            for order in open_orders:
                symbol = order.get("symbol")
                if not symbol:
                    continue  # Skip orders without a symbol

                limit_price = float(order.get("limit_price") or 0)
                stop_price = float(order.get("stop_price") or 0)

                # Get latest price
                latest_price = get_last_ask_price(ib, symbol)

                # Calculate risk
                risk = 0
                if latest_price:
                    if stop_price:
                        risk = round(latest_price - stop_price, 2)
                    elif limit_price:
                        risk = round(latest_price - limit_price, 2)
                risk = abs(risk)

                # Calculate position size for the single tier in config
                tier_sizes = {}
                if risk:
                    trading_tiers = config.get("Trading_Tiers", {})
                    if trading_tiers:
                        tier, value = next(iter(trading_tiers.items()))
                        tier_sizes[tier] = abs(int(round(value / risk)))

                # Append row
                entry = {
                    "symbol": symbol,
                    "limit_price": limit_price,
                    "stop_price": stop_price,
                    "latest_price": latest_price,
                    "risk": risk,
                }
                entry.update(tier_sizes)
                data.append(entry)

        # Return DataFrame
        df = pd.DataFrame(data)
        return df

    except Exception as e:
        print(f"Error processing open orders: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error



 
# Main function
def process_open_orders(ib,project_config):
    
    """Main function to process open orders, fetch prices, calculate risk, and write to the database."""

    open_orders = get_open_orders(project_config)
    df = handle_orders_data(open_orders,project_config,ib)

    return df


