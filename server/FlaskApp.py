from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from db_LiveDataStream import get_those_alarms
import threading
from ibapi.client import *
from ibapi.wrapper import *
from IBApp import IbapiApp
from IBasync import *
import asyncio
import pandas as pd
from psycopg2.pool import SimpleConnectionPool
import subprocess
import psutil

from Calculate import calculate_position_size


from ConfigFiles import read_project_config
from ConfigFiles import read_database_config

from OpenOrdersAlpaca import process_open_orders
from waitress import serve
# Load configs
project_config = read_project_config(filename='config.json')
database_config = read_database_config(filename="database.ini", section="postgresql")

# Nää ei saa mennä sekaisin, koska delete ominaisuus
database_livestream_config = read_database_config(filename="database.ini", section="livestream")

# app instance

RISK = project_config["Risk"]


app = Flask(__name__)
CORS(app)



host = project_config["ib_connection"]["host"]
port = project_config["ib_connection"]["port"]
clientId = project_config["ib_connection"]["clientId"]

# Initialize the connection pool
db_pool = SimpleConnectionPool(1, 10, **database_config)  # Min 1, Max 10 connections

def get_db_connection():
    """Get a database connection from the pool."""
    return db_pool.getconn()

def release_db_connection(conn):
    """Return the connection to the pool."""
    db_pool.putconn(conn)


# Live-trading-assistance-------------------------------------------------------------


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

@app.route('/run-script', methods=['POST'])
def run_script():
    data = request.json
    param = data.get('param')
    print(project_config["TARGET_SCRIPT"])
    print(project_config["SCRIPT_DIR"])
    try:
        if is_process_running():
            print(f"{project_config["TARGET_SCRIPT"]} is already running. Terminating it...")
            terminate_exact_process()
            time.sleep(2)

        subprocess.Popen(
            [
                'cmd.exe', '/c',
                f'start cmd.exe /k python {project_config["TARGET_SCRIPT"]} {param}'
            ],
            cwd=project_config["SCRIPT_DIR"],
            shell=True
        )

        time.sleep(5)

        if is_process_running():
            response = {'output': f"LiveStream ticker: {param.upper()} started"}
            print(f"Response: {response}")
            return jsonify(response), 200
        else:
            response = {'error': f"The {project_config["TARGET_SCRIPT"]} process is not running."}
            print(f"Response: {response}")
            return jsonify(response), 500

    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500

def is_process_running():
    """Check if LiveDataStreamer.py is running."""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and project_config["TARGET_SCRIPT"] in ' '.join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def terminate_exact_process():
    """Terminate all python processes running LiveDataStreamer.py."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' and project_config["TARGET_SCRIPT"] in ' '.join(proc.info['cmdline']):
                psutil.Process(proc.info['pid']).terminate()
                print(f"Terminated {project_config["TARGET_SCRIPT"]} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Error terminating process: {e}")

@app.route('/check-streamer', methods=['GET'])
def check_streamer_status():
    return jsonify({'running': is_process_running()})

#--------------------------------------------------------------------------------------






# Risk-levels--------------------------------------------------------------------------

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





@app.route("/api/open-alpaca-orders", methods=['GET'])
def get_alpacaorders_data():
    ib = IB()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(ib.connectAsync(host, port, clientId))
        
        df1= process_open_orders(ib, project_config)
        print(df1)

        if df1.empty:
            return jsonify({'status': 'success', 'message': 'No open orders'}), 200
        return jsonify({'status': 'success', 'data': df1.to_dict(orient='records')})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        ib.disconnect()
        loop.close()

@app.route("/api/place-order", methods=['POST'])
def place_order():
    ib = IB()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Connect synchronously using the new loop
        ib.connect(host, port, clientId)

        # --- Your business logic ---
        symbol, action, position_size, entry_price, stop_price = handle_order_request()

        entry_price = get_last_ask_price(ib, symbol) or entry_price
        position_size = calculate_position_size(entry_price, stop_price, RISK)

        if position_size <= 0:
            return jsonify({"error": "Calculated position size <= 0"}), 400

        parent, stoploss = place_bracket_order(
            ib=ib,
            symbol=symbol,
            action=action,
            quantity=position_size,
            limit_price=entry_price,
            stop_price=stop_price
        )

        return jsonify({
            "message": "Order placed successfully!",
            "symbol": symbol,
            "action": action,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "parent_orderId": getattr(parent, 'orderId', None),
            "stop_orderId": getattr(stoploss, 'orderId', None)
        }), 200

    except Exception as e:
        print("Error placing order:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        ib.disconnect()
        loop.close()

            
@app.route("/api/ib_accountdata", methods=['GET']) # IB connection
def get_ib_portfolio():
    try:
        IB_app = IbapiApp()
        IB_app.connect(host, port, clientId)
        threading.Thread(target=IB_app.run, daemon=True).start()

        if IB_app.connected_flag.wait(timeout=1):
            print("Connection confirmed.")

            positions_df = IB_app.get_positions()
            orders_df = IB_app.get_stopOrders()
            accountdata_df = IB_app.get_accountdata()

            # Filter accountdata_df for only USD StockMarketValue and TotalCashBalance
            filtered_accountdata_df = accountdata_df[
                ((accountdata_df['Key'] == 'StockMarketValue') & (accountdata_df['Currency'] == 'USD')) |
                ((accountdata_df['Key'] == 'TotalCashBalance') & (accountdata_df['Currency'] == 'USD'))
            ]

            # ✅ Call handle_open_risk with DataFrames, not lists
            risk_levels = handle_open_risk(positions_df, orders_df)


            # Convert DataFrames to dicts for JSON serialization
            positions_data = positions_df.to_dict(orient="records")
            orders_data = orders_df.to_dict(orient="records")
            accountdata = filtered_accountdata_df.to_dict(orient="records")
            risk_data = risk_levels.to_dict(orient="records")

            return jsonify({
                "positions": positions_data,
                "orders": orders_data,
                "accountdata": accountdata,
                "risk_levels": risk_data
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
            print("Disconnected from IB Gateway/TWS.")





    


# Run Flask and IB API simultaneously
if __name__ == "__main__":
    # Serve the app with Waitress on all interfaces
    serve(app, host="0.0.0.0", port=8080)
    # Run Flask app (use built-in dev server for development)
   # app.run(host="0.0.0.0", port=8080, debug=True)