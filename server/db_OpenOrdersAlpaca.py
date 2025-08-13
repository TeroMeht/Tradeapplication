import requests
import pandas as pd
from IBApp import IbapiApp
import threading
import time


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

def handle_orders_data(open_orders,config):
    """Processes open orders and returns a pandas DataFrame with calculated values."""

    # Initialize list to hold data
    data = []
    
    if open_orders is not None:
        for order in open_orders:
            symbol = order.get("symbol")
            limit_price = order.get("limit_price") or 0  # Default to 0 if None or invalid
            stop_price = order.get("stop_price") or 0   # Default to 0 if None or invalid
            latest_price = get_latest_price(symbol, config) or 0  # Default to 0 if None or invalid Tämä vaatii IB yhteyden

            # Calculate risk
            risk = 0
            if latest_price:
                if stop_price:
                    risk = round(latest_price - float(stop_price), 2)
                elif limit_price:
                    risk = round(latest_price - float(limit_price), 2)

            # Always take the absolute value of risk
            risk = abs(risk)

            # Calculate position size for the single tier in config and round to full number
            tier_sizes = {}
            if risk:
                trading_tiers = config.get("Trading_Tiers", {})

                # Assuming only one tier exists
                if trading_tiers:
                    tier, value = next(iter(trading_tiers.items()))
                    tier_sizes[tier] = abs(int(round(value / risk)))  # round to nearest whole number

            # Append data
            entry = {
                "symbol": symbol,
                "limit_price": limit_price,
                "stop_price": stop_price,
                "latest_price": latest_price,
                "risk": risk,
            }
            entry.update(tier_sizes)
            data.append(entry)
    
    # Create a DataFrame from the collected data
    df = pd.DataFrame(data)
    return df

def get_latest_price(symbol, config):
    host = config["ib_connection"]["host"]
    port = config["ib_connection"]["port"]
    clientId = config["ib_connection"]["clientId"]

    try:
        # Initialize and connect the IB API application
        IB_app = IbapiApp()
        IB_app.connect(host, port, clientId)
        threading.Thread(target=IB_app.run, daemon=True).start()
        time.sleep(1)

        # Fetch contract details for the given symbol
        mycontract = IB_app.get_contract(symbol)
        print("IB Contract:", mycontract)  # Print IB contract details
        # Fetch historical price data
        last_price = IB_app.get_lastPrice(99, mycontract)
        print("Last Price from IB:", last_price)  # Print last price from IB
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        last_price = None
    finally:
        # Ensure the connection is closed
        IB_app.disconnect()


    return last_price


# Main function
def process_open_orders(config):
    
    """Main function to process open orders, fetch prices, calculate risk, and write to the database."""

    open_orders = get_open_orders(config)
    df = handle_orders_data(open_orders,config)

    return df


