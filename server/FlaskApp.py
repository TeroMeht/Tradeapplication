from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from db_OpenOrdersAlpaca import process_open_orders
from db_Strategydev import get_setup_data, get_price_data
from db_LiveDataStream import get_livestream_data
from db_LiveDataStream import get_those_alarms
from db_Executions import get_execution_data, get_trade_data
from db_DailypnlLimit import get_all_pnls
from db_PortfolioControlSystem import pcs_handler
import threading
from ibapi.client import *
from ibapi.wrapper import *
from IBApp import IbapiApp
import pandas as pd
from config import read_project_config, read_db_config
from psycopg2.pool import SimpleConnectionPool
import subprocess
import psutil
import os


config = read_project_config('config.json')
# app instance

app = Flask(__name__)
CORS(app)

DAILY_LOSS_LIMIT = -1000.0  # Example: stop trading if loss exceeds -1000

host = config["ib_connection"]["host"]
port = config["ib_connection"]["port"]
clientId = config["ib_connection"]["clientId"]

# Initialize the connection pool
db_config = read_db_config()
db_pool = SimpleConnectionPool(1, 10, **db_config)  # Min 1, Max 10 connections

def get_db_connection():
    """Get a database connection from the pool."""
    return db_pool.getconn()

def release_db_connection(conn):
    """Return the connection to the pool."""
    db_pool.putconn(conn)

# Apufunktiot place orderille
def handle_order_request():

    try:
        # Parse JSON data from the request
        data = request.json

        # Validate required fields
        required_fields = ['symbol', 'entry_price', 'lmt_price', 'stp_price', 'position_size']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Extract the order data from the request
        symbol = data['symbol']
        entry_price = float(data['entry_price'])  # Convert entry_price to float
        lmt_price = float(data['lmt_price'])      # Convert lmt_price to float
        stp_price = float(data['stp_price'])      # Convert stp_price to float
        position_size = int(data['position_size'])  # Convert position_size to int

        # Determine the value for the final stop price
        stop_price = stp_price if stp_price != 0 else lmt_price


        # Determine action and order type based on price conditions
        if entry_price > lmt_price or stp_price:  # If entry price is higher than both limit and stop price
            action = 'BUY'
        elif entry_price < lmt_price or stp_price:  # If entry price is lower than both limit and stop price
            action = 'SELL'
        else:
            # If no condition is met (e.g., entry price is between limit and stop prices)
            raise ValueError("Invalid price conditions. Entry price does not match expected thresholds.")
        

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    # Return the values directly
    return symbol, action, position_size, entry_price, stop_price

def handle_open_risk(positions_df: pd.DataFrame, orders_df: pd.DataFrame) -> pd.DataFrame:
    # Initialize an empty DataFrame for the results
    risk_df = pd.DataFrame(columns=["OrderId", "Symbol", "AvgCost", "AuxPrice", "Position", "OpenRisk"])

    # Iterate over positions
    row_index = 0  # Track the index for appending rows
    for _, position_row in positions_df.iterrows():
        
        symbol = position_row["Symbol"]
        position = position_row["Position"]
        avgcost = position_row["AvgCost"]

        # Find the matching order for this symbol with OrderType 'STP'
        matching_orders = orders_df[(orders_df["Symbol"] == symbol) & (orders_df["OrderType"] == "STP")].head(1)

        if not matching_orders.empty:
            for _, order_row in matching_orders.iterrows():
                orderId = order_row["OrderId"]
                aux_price = order_row["AuxPrice"]
                open_risk = abs(position * (aux_price - avgcost))
                open_risk = round(open_risk, 2)
        else:
            # No STP order found, set OpenRisk to infinity
            orderId = 0
            aux_price = 0
            open_risk = str('inf')

        # Add the result to the risk DataFrame using loc
        risk_df.loc[row_index] = {
            "OrderId": orderId,
            "Symbol": symbol,
            "AuxPrice": aux_price,
            "AvgCost": avgcost,
            "Position": position,
            "OpenRisk": open_risk
        }
        row_index += 1

    return risk_df


# Home page codes
@app.route("/api/executions", methods=['GET'])
def get_executions():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch all data from the livestreamdata table
        df = get_execution_data(cursor)

        # Convert DataFrame to a dictionary and return it as a JSON response
        return jsonify(df)

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

@app.route("/api/trades", methods=['GET'])
def get_trades():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        trades = get_trade_data(cursor)
        return jsonify(trades)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)




# Risk-levels
@app.route("/api/openorders", methods=['GET'])
def get_alpacaorders_data(): # IB connection
     
    try:
        df = process_open_orders(config)

        # Check if DataFrame is empty
        if df.empty:
            print("No open Alpaca orders")
            return jsonify({'status': 'success', 'message': 'No open orders'}), 200
        
        # Convert DataFrame to dictionary format
        data = df.to_dict(orient='records')
        return jsonify({'status': 'success', 'data': data})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Risk-levels
@app.route("/api/place-order", methods=['POST']) # IB connection
def place_order():
    try:

        IB_app = IbapiApp()
        IB_app.connect(host, port, clientId)
        threading.Thread(target=IB_app.run, daemon=True).start()

        # Wait for connection confirmation via nextValidId()
        if IB_app.connected_flag.wait(timeout=2):
            print("Connection confirmed.")
            symbol, action, position_size, entry_price, stop_price = handle_order_request()

            mycontract = IB_app.get_contract(symbol) # tämä käy kysymässä contractin IB_appilta
            # Request PnL data for reqId=17005
            IB_app.place_order(mycontract, action,position_size, entry_price, stop_price,ordertype = 'LMT')

            print("Order going live, with price:",entry_price) # tää tarvii kysyä just ennen ku tilaus lähtee ja mennä sillä arvolla
        else:
            print("Failed to confirm connection (timeout). Disconnecting...")
            IB_app.disconnect()
            raise ConnectionError("IB connection timeout — exiting process.")

        # Assuming the order is successfully placed:
        return jsonify({"message": "Order placed successfully!", "symbol": symbol, "action": action}), 200

    except Exception as e:
        # Handle errors if any occurred during order placement
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        if IB_app.isConnected():
            IB_app.disconnect()
            print("Place order disconnect from IB Gateway/TWS.")
            
# Risk-levels
@app.route("/api/ib-positions", methods=['GET']) # IB connection
def get_ibpositions_data():

    try:
        IB_app = IbapiApp()
        IB_app.connect(host, port, clientId)
        threading.Thread(target=IB_app.run, daemon=True).start()

        # Wait for connection confirmation via nextValidId()
        if IB_app.connected_flag.wait(timeout=2):
            print("Connection confirmed.")
            # Fetch portfolio positions
            positions= IB_app.get_positions()

            orders= IB_app.get_stopOrders()

            risk_levels = handle_open_risk(positions,orders)
            print(risk_levels)
            risk_data = risk_levels.to_dict(orient='records')  # Convert risk DataFrame to list of dicts


        else:
            print("Failed to confirm connection (timeout). Disconnecting...")
            IB_app.disconnect()
            raise ConnectionError("IB connection timeout — exiting process.")
        
        # Return all data in JSON format
        return jsonify({
            "openRiskLevels": risk_data
        }), 200

    except Exception as e:
        # Handle errors if any occurred during order placement
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    finally:
        if IB_app.isConnected():
            IB_app.disconnect()
            print("Positions and orders disconnect from IB Gateway/TWS.")





# Strategy-development
@app.route("/api/query", methods=['GET'])
def get_query_setupdata():
    try:
        # Extract 'userId' from the query parameters
        user_id = request.args.get('userId')
        # Check if 'userId' is provided
        if not user_id:
            return jsonify({'status': 'error', 'message': 'userId is required'}), 400
        
        # Call a function to fetch data using the user_id
        df = get_setup_data(user_id)
 
        # Check if the DataFrame is empty (no data found for the user_id)
        if df.empty:
            return jsonify({'status': 'success', 'message': 'No data available for the provided userId'}), 200
        
        # Convert the DataFrame to a dictionary (for the response)
        data = df.to_dict(orient='records')
        return jsonify({'status': 'success', 'data': data})

    except Exception as e:
        # Catch any exceptions and return an error message
        return jsonify({'status': 'error', 'message': str(e)}), 500
# Strategy-development
@app.route("/api/chart-data", methods=['GET'])
def get_chart_data_endpoint():
    try:
        # Retrieve query parameters
        ticker = request.args.get('ticker')
        date_str = request.args.get('date')  
        marketdata = request.args.get('timeframe')
        print(ticker, date_str,marketdata)


        # Fetch the chart data based on the parameters (replace this with your actual data source)
        data = get_price_data(ticker, date_str, marketdata)

        # Prepare the data for JSON response
        chart_data = []
        for item in data:
            chart_data.append({
                'Time': item['Time'].strftime("%H:%M:%S"),  # Ensure 'time' is in the correct string format (YYYY-MM-DD)
                'Open': item['Open'],
                'High': item['High'],
                'Low': item['Low'],
                'Close': item['Close'],
                'Volume': item['Volume'],
                'VWAP': item['VWAP'],
                'EMA9': item['EMA9']
            })
        print(chart_data)
        # Return the chart data as JSON
        return jsonify({
            'status': 'success',
            'ohlcData': chart_data  # Respond with the OHLC data
        })
    except Exception as e:
        # Handle unexpected errors
        return jsonify({'status': 'error', 'message': str(e)}), 500




# Live-trading-assistance
@app.route("/api/livestream", methods=['GET'])
def get_livestreamdata():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch all data from the livestreamdata table
        df = get_livestream_data(cursor)

        # Convert DataFrame to a dictionary and return it as a JSON response
        return jsonify(df)

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)
    
# Live assistance alarms
@app.route("/api/alarms", methods=['GET'])
def get_alarms():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch all alarms from the alarms table
        alarms = get_those_alarms(cursor)
        
        # Return alarms as JSON response
        return jsonify(alarms)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)

TARGET_SCRIPT = "LiveDataStreamer.py"
SCRIPT_DIR = r"C:/Projects/05_TradingAssistance"

@app.route('/run-script', methods=['POST'])
def run_script():
    data = request.json
    param = data.get('param')

    try:
        if is_process_running():
            print(f"{TARGET_SCRIPT} is already running. Terminating it...")
            terminate_exact_process()
            time.sleep(2)

        subprocess.Popen(
            [
                'cmd.exe', '/c',
                f'start cmd.exe /k python {TARGET_SCRIPT} {param}'
            ],
            cwd=SCRIPT_DIR,
            shell=True
        )

        time.sleep(5)

        if is_process_running():
            response = {'output': f"LiveStream ticker: {param.upper()} started"}
            print(f"Response: {response}")
            return jsonify(response), 200
        else:
            response = {'error': f"The {TARGET_SCRIPT} process is not running."}
            print(f"Response: {response}")
            return jsonify(response), 500

    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500


def is_process_running():
    """Check if LiveDataStreamer.py is running."""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and TARGET_SCRIPT in ' '.join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def terminate_exact_process():
    """Terminate all python processes running LiveDataStreamer.py."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and TARGET_SCRIPT in ' '.join(proc.info['cmdline']):
                psutil.Process(proc.info['pid']).terminate()
                print(f"Terminated {TARGET_SCRIPT} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Error terminating process: {e}")


@app.route('/check-streamer', methods=['GET'])
def check_streamer_status():
    return jsonify({'running': is_process_running()})




# Portfolio control system
# Valvoo ettei portfoliossa ole positioita ilman stoppia, sulkee ne väkisin jos on
@app.route('/api/run_pcs_logic', methods= ['GET']) # IB connection
def pcs_logic():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        pcs_handler(cursor)  # Just call your handler
        conn.commit()
        return jsonify({"status": "PCS handler executed successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        release_db_connection(conn)

    # # Hakee portfolion ja avoimet orderit
    # portfolio = get_ib_positions_from_api()
    # #executions = get_ib_executions_from_api()

    # if portfolio is not None:
    #     positions = portfolio.get("openRiskLevels", [])
        
    #     if positions:
    #         # Create DataFrame with the columns: Symbol, Position, AvgCost, OpenRisk
    #         df = pd.DataFrame(positions)
    #         print("\nCurrent IB Positions (Portfolio):")
    #         print(df.to_string(index=False))  # Print the DataFrame without index

    #     # Detect positions with infinite risk (i.e., no stop-loss)
    #     risky_positions = detect_inf_risk_positions(portfolio)

    #     if risky_positions:
    #         print("Risky positions detected:", risky_positions)
            
    #         for position in risky_positions:
    #             symbol = position.get("symbol")
    #             qty = position.get("qty")
    #             avg_price = position.get("avg_price")
                
    #             print(f"⚠️ Closing risky position: {symbol} (Qty: {qty}, Avg Price: {avg_price})")

    #             try:
    #                 # Initialize the IB API connection
    #                 IB_app = IbapiApp()
    #                 IB_app.connect(host, port, clientId)
    #                 threading.Thread(target=IB_app.run, daemon=True).start()

    #                 # Wait for connection confirmation via nextValidId()
    #                 if IB_app.connected_flag.wait(timeout=2):
    #                     print("Connection confirmed.")
                        
    #                     # Use the force_exit_position method to close the risky position
    #                     action = "SELL" if qty > 0 else "BUY"  # If position is long, sell; if short, buy
    #                     position_size = abs(qty)  # Use absolute value to close position
                        
    #                     # Get the contract information for the symbol
    #                     mycontract = IB_app.get_contract(symbol)

    #                     # Force exit the position with a market order
    #                     IB_app.place_market_order(mycontract, action, position_size)
    #                     print(f"Market order placed to force exit position {symbol}.")

    #                 else:
    #                     print("Failed to confirm connection (timeout). Disconnecting...")
    #                     IB_app.disconnect()
    #                     raise ConnectionError("IB connection timeout — exiting process.")

    #             except Exception as e:
    #                 print(f"An error occurred while placing market order for {symbol}: {str(e)}")
    #                 return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    #             finally:
    #                 if IB_app.isConnected():
    #                     IB_app.disconnect()
    #                     print("Force exit disconnect from IB Gateway/TWS.")
            
    #         return jsonify({
    #             "status": "success",
    #             "message": f"{len(risky_positions)} force market orders sent"
    #         }), 200

    #     else:
    #         return jsonify({"status": "success", "message": "No risky positions detected"}), 200

    # else:
    #     return jsonify({"status": "error", "message": "Failed to fetch positions"}), 500
    

# Täällä kysytään kerralla kaikki oleellinen IB:ltä jotta sitä ei tarvitse erikseen kysellä joka välissä
# Executionit viedään kantaan tästä samasta viestistä
# Positions näytetään
# Orders näytetään
# pnl sama homma?    
@app.route("/api/ib_portfoliodata", methods=['GET'])
def get_ib_portfolio():
    try:
        # Create and connect the IB API instance
        IB_app = IbapiApp()
        IB_app.connect(host, port, clientId)

        # Start the IB API thread
        threading.Thread(target=IB_app.run, daemon=True).start()

        # Wait for connection confirmation
        if IB_app.connected_flag.wait(timeout=2):
            print("Connection confirmed.")

            # Fetch the data
            executions_df, commissions_df = IB_app.get_executions()
            positions_df = IB_app.get_positions()
            orders_df = IB_app.get_stopOrders()

            # Ensure numeric types
            # Ensure numeric types
            executions_df["AvgPrice"] = executions_df["AvgPrice"].astype(float)
            executions_df["Shares"] = executions_df["Shares"].astype(float)
            commissions_df["Commission"] = commissions_df["Commission"].astype(float)

            # Merge executions and commissions by ExecId
            merged_df = executions_df.merge(
                commissions_df,
                how="left",
                left_on="ExecId",
                right_on="ExecId"
            )

            # Calculate adjusted average price
            merged_df["AdjustedAvgPrice"] = merged_df["AvgPrice"] + (merged_df["Commission"] / merged_df["Shares"])

            # Drop unwanted columns (handle missing ones safely)
            merged_df.drop(columns=["RealizedPNL", "Yield", "YieldRedemptionDate", "Currency", "ExecId"], inplace=True, errors="ignore")

            # Prepare clean outputs
            executions_data = merged_df.to_dict(orient="records")
            positions_data = positions_df.to_dict(orient="records")
            orders_data = orders_df.to_dict(orient="records")

            return jsonify({
                "executions": executions_data,
                "positions": positions_data,
                "orders": orders_data
            }), 200


        else:
            print("Failed to confirm connection (timeout). Disconnecting...")
            IB_app.disconnect()
            raise ConnectionError("IB connection timeout — exiting process.")

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        if IB_app.isConnected():
            IB_app.disconnect()
            print("Executions disconnect from IB Gateway/TWS.")


# Palauttaa PCS hälytykset omasta kannasta
@app.route("/api/pcs_alarms", methods=['GET'])
def get_pcs_alarms():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Use exact case-sensitive column names in quotes
        cursor.execute('SELECT id, "Message", "Status", "Date" FROM pcs_alarms ORDER BY id;')
        rows = cursor.fetchall()

        alarms = [
            {
                "id": row[0],
                "Message": row[1],
                "Status": row[2],
                "Date": row[3].isoformat() if row[3] else None
            }
            for row in rows
        ]

        return jsonify(alarms)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        release_db_connection(conn)






# Daily pnl
@app.route('/api/dailypnl', methods=['GET'])
def last_pnl_endpoint():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch all PnL data
        all_pnls = get_all_pnls(cursor)

        if all_pnls:
            last_pnl = all_pnls[0]  # Most recent entry

            # Extract DailyPnL and Time
            daily_pnl = last_pnl.get("DailyPnL")
            timestamp = last_pnl.get("Time")  # Already formatted in get_all_pnls()

            # Check against limit
            if daily_pnl is not None:
                limit_exceeded = daily_pnl < DAILY_LOSS_LIMIT
            else:
                limit_exceeded = None

            # Include the limit status and timestamp in the response
            response = {
                "pnl": daily_pnl,
                "limitExceeded": limit_exceeded,
                "limitThreshold": DAILY_LOSS_LIMIT,
                "timestamp": timestamp
            }

            return jsonify(response), 200

        else:
            return jsonify({"error": "No PnL data found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        release_db_connection(conn)




# Run Flask and IB API simultaneously
if __name__ == "__main__":
    app.run(debug=False, port=8080)