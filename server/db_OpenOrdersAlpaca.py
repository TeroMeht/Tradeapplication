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

            # Calculate position sizes based on dynamic tiers from config and round
            tier_sizes = {}
            if risk and risk != 0:
                # Use only the "Trading_Tiers" section from the config
                trading_tiers = config.get("Trading_Tiers", {})

                for tier, value in trading_tiers.items():
                    tier_sizes[tier] = abs(int(round(value / risk, -1)))

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


# Kantakoodit jotka eivät nyt ole käytössä
# def delete_missing_symbols_from_db(df,conn,cursor):
#     """Deletes rows from the PostgreSQL database where the symbol no longer exists in the DataFrame."""

#     # Get all symbols currently in the database
#     get_db_symbols_query = "SELECT symbol FROM open_orders;"
#     cursor.execute(get_db_symbols_query)
#     db_symbols = {row[0] for row in cursor.fetchall()}  # Set of symbols from the database

#     # Get all symbols from the DataFrame
#     df_symbols = set(df['Symbol'])  # Set of symbols from the DataFrame

#     # Find symbols that exist in the database but not in the DataFrame
#     symbols_to_delete = db_symbols - df_symbols  # Symbols in DB but not in the DataFrame

#     if symbols_to_delete:
#         # Delete rows for these symbols
#         delete_query = "DELETE FROM open_orders WHERE symbol = %s;"
#         for symbol in symbols_to_delete:
#             cursor.execute(delete_query, (symbol,))
#         conn.commit()
#         print(f"Deleted order for symbol: {symbol}")
#     else:
#         pass

# def return_db_data(conn,cursor):
#     """
#     Fetches data from the database using a cursor and returns it as a DataFrame.

#     Returns:
#     pd.DataFrame: DataFrame containing the query results.
#     """

#     # SQL query to fetch data
#     query = """
#     SELECT * FROM open_orders;  -- Replace with your actual table and column names
#     """

#     # Execute the query
#     cursor.execute(query)

#     # Fetch all rows and column names
#     rows = cursor.fetchall()
#     columns = [desc[0] for desc in cursor.description]

#     # Create a DataFrame from the query result
#     df = pd.DataFrame(rows, columns=columns)

#     # Return the DataFrame
#     return df

# def write_db(row, conn, cursor):

#     # Define the SQL query for insertion
#     insert_query = """
#     INSERT INTO open_orders (symbol, limit_price, stop_price, latest_price, risk, tier_1, tier_2, tier_3, tier_4)
#     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#     ON CONFLICT (symbol) DO NOTHING;
#     """ #tällä on conflict pakotetaan ettei kannassa voi olla kuin uniikkeja tickereitä
    
#     try:
#        # Extract values from the row (with capitalized column headers)
#         values = (row['Symbol'], row['Limit Price'], row['Stop Price'], row['Latest Price'], row['Risk'],
#                   row['Tier 1'], row['Tier 2'], row['Tier 3'], row['Tier 4'])
        
        
#         # Execute the insert query for the current row
#         cursor.execute(insert_query, values)
        
#         # Commit the changes to the database
#         conn.commit()
#         print(print(f"Inserted order for symbol: {row['Symbol']}"))
    
#     except Exception as e:
#         conn.rollback()  # Rollback in case of error
#         print(f"An error occurred while inserting row for symbol {row['Symbol']}: {e}")

# def update_order_in_db(row, conn, cursor):
#     """
#     Updates an existing order in the 'open_orders' table using values from the DataFrame row.
    
#     :param row: A row from the DataFrame containing the order data.
#     :param conn: The database connection object.
#     :param cursor: The database cursor object.
#     """
#     # Define the update query for existing rows
#     update_query = """
#     UPDATE open_orders
#     SET limit_price = %s, stop_price = %s, latest_price = %s, risk = %s, 
#         tier_1 = %s, tier_2 = %s, tier_3 = %s, tier_4 = %s
#     WHERE symbol = %s;
#     """
    
#     # Extract the values from the DataFrame row
#     limit_price = row['Limit Price']
#     stop_price = row['Stop Price']
#     latest_price = row['Latest Price']
#     risk = row['Risk']
#     tier_1 = row['Tier 1']
#     tier_2 = row['Tier 2']
#     tier_3 = row['Tier 3']
#     tier_4 = row['Tier 4']
#     symbol = row['Symbol']

#     # Execute the update query
#     try:
#         cursor.execute(update_query, (limit_price, stop_price, latest_price, risk,
#                                       tier_1, tier_2, tier_3, tier_4, symbol))
#         print(f"Updated order for symbol: {symbol}")
#     except Exception as e:
#         print(f"Error updating order for symbol {symbol}: {e}")
#         conn.rollback()  # Rollback in case of error

#     # Commit the changes to the database
#     conn.commit()

# def delete_all_open_orders(conn,cursor):

#     # SQL command to empty the open_orders table
#     delete_query = "DELETE FROM open_orders;"
#     cursor.execute(delete_query)

#     conn.commit()

#     print("Open orders is now empty")

# def get_all_symbols(conn, cursor):
#     """
#     Returns all symbols from the specified table.

#     :param conn: The database connection object.
#     :param cursor: The database cursor object.
#     :param table_name: The name of the table to fetch data from.
#     :return: A list of symbols from the table.
#     """
#     # Define the SQL query to select all symbols from the table
#     query = "SELECT symbol FROM open_orders;"

#     # Execute the query
#     cursor.execute(query)
    
#     # Fetch all results
#     symbols = cursor.fetchall()

#     # Extract the symbol values from the results
#     symbol_list = [symbol[0] for symbol in symbols]  # Assuming 'symbol' is the column name

#     return symbol_list





# Main function
def process_open_orders(config):
    
    """Main function to process open orders, fetch prices, calculate risk, and write to the database."""

    open_orders = get_open_orders(config)

    df = handle_orders_data(open_orders,config)

    return df

# # tässä kohtaa muodostetaan kantayhteys ja se passataan kantaa käsitteleville funktioille     
#     try:
#         # Database connection settings
#         conn = connect_db()
#         cursor = conn.cursor()

# # Tämä on tyhjä jos Alpacassa ei ole tilauksia 
#         if df is None or df.empty:
#             # Write to PostgreSQL database
#             print("No open orders.")

#             delete_all_open_orders(conn,cursor)
#             latest_data_from_db = pd.DataFrame()


#         else:
#             symbol_listdb = get_all_symbols(conn,cursor) # mitä databasessa jo. jos mätsää niin pitää updatee jos ei niin kirjoita
#                 # Loop through the symbols in the DataFrame

#             for _, row in df.iterrows():
#                 symbol = row['Symbol']
#                 # Check if the symbol is in the database
#                 if symbol in symbol_listdb: # jos löytyy dataframesta ja kannasta
#                     update_order_in_db(row, conn, cursor)
#                 else:                       # jos löytyy dataframesta, mutta ei kannasta
#                     write_db(row,conn,cursor)
#                     # Delete rows for symbols that are no longer in the DataFrame              
#             delete_missing_symbols_from_db(df,conn,cursor)
#             latest_data_from_db = return_db_data(conn,cursor)
            
#     except Exception as e:
#         print(f"An error occurred while connecting to the database: {e}")
#     finally:
#         cursor.close()
#         conn.close()
#         print(f"Closing database connection")


#     return latest_data_from_db

