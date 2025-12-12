from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import subprocess
from dataclasses import asdict
from waitress import serve



from common.logger import setup_logging
import logging
setup_logging()
logger = logging.getLogger(__name__)
logger.info("Application backend starting")


from pathlib import Path
from common.calculate import calculate_position_size
from common.read_configs_in import *
from database.db_functions import *
from alpacaAPI import process_open_orders
from ibclient import *
from helpers.handle_place_order import *
from helpers.handle_open_risks import handle_open_risk
from helpers.detect_stoplevel import detect_stoplevel
from helpers.handle_executions import is_entry_allowed
from helpers.utils import log_scan_results, sanitize_for_json
from scanner.scan import run_scanner
from helpers.handle_market_scan import *



# Load configs
project_config = read_project_config(filename='config.json')
database_config = read_database_config(filename="database.ini", section="livestream")

app = Flask(__name__)
CORS(app)


@app.route("/api/input_tickers", methods=["GET"])
def get_input_tickers():
    try:
        # Get base path from project_config
        base_path = Path(project_config["input_tickers"])
        if not base_path.exists() or not base_path.is_dir():
            return jsonify({"error": f"Base path not found or is not a directory: {base_path}"}), 500

        # If a specific file is requested, read only that file
        filename = request.args.get("file")
        if filename:
            file_path = base_path / filename
            if not file_path.exists() or not file_path.is_file():
                return jsonify({"error": f"File not found: {file_path}"}), 404

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return jsonify({"filename": filename, "content": content})

        # Otherwise, read all .txt files in the directory
        files = list(base_path.glob("*.txt"))
        result = {}
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                result[file.name] = f.read()

        return jsonify({"files": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/input_tickers", methods=["POST"])
def save_input_tickers():
    try:
        data = request.get_json()
        if not data or "file" not in request.args or "content" not in data:
            return jsonify({"error": "Missing 'file' query param or content in body"}), 400

        filename = request.args["file"]
        content = data["content"]

        base_path = Path(project_config["input_tickers"])
        if not base_path.exists() or not base_path.is_dir():
            return jsonify({"error": f"Base path not found: {base_path}"}), 500

        file_path = base_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return jsonify({"success": True, "filename": filename})

    except Exception as e:
        return jsonify({"error": str(e)}), 500






@app.route("/api/alarms", methods=['GET'])
def get_alarms():
    try:
        # Fetch alarms using your helper
        alarms = fetch_alarms(database_config)

        if alarms is None:
            logger.error("Failed to fetch alarms.")
            return jsonify({"error": "Failed to fetch alarms."}), 500

        # Convert any date/time objects to strings
        for alarm in alarms:
            for key in ['Date', 'Time']:
                if key in alarm and not isinstance(alarm[key], str):
                    alarm[key] = str(alarm[key])

        return jsonify(alarms), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tables", methods=['GET'])
def get_table_names():
    """
    Fetch all table names from the database (excluding 'livedata' and 'alarms')
    and return them as JSON.
    """
    try:
        tables = fetch_all_table_names(database_config)

        if not tables:
            logger.warning("No tables found or failed to fetch.")
            return jsonify({"error": "No tables found."}), 404

        return jsonify({"tables": tables}), 200

    except Exception as e:
        logger.error(f"Error fetching table names: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tables/last_rows", methods=['GET'])
def get_last_rows():
    """
    Fetch the last row from each table (excluding 'livedata' and 'alarms')
    and return them as JSON.
    """
    try:
        last_rows = fetch_last_row_from_each_table(database_config)

        if not last_rows:
            logger.warning("No data found or failed to fetch last rows.")
            return jsonify({"error": "No data found."}), 404

        return jsonify({"last_rows": last_rows}), 200

    except Exception as e:
        logger.error(f"Error fetching last rows: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        target_script = project_config["TARGET_SCRIPT"]
        script_dir = project_config["SCRIPT_DIR"]

        logger.info(f"Starting script: {target_script} in {script_dir}")

        subprocess.Popen(
            [
                'cmd.exe', '/c',
                f'start cmd.exe /k python {target_script}'
            ],
            cwd=script_dir,
            shell=True
        )

        return jsonify({'output': f"{target_script} started successfully."}), 200

    except Exception as e:
        logger.error(f"Error starting script: {e}")
        return jsonify({'error': str(e)}), 500

#--------------------------------------------------------------------------------------






# Risk-levels--------------------------------------------------------------------------








@app.route("/api/open-alpaca-orders", methods=['GET'])
def get_alpacaorders_data():
    ib = IB()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:

        ib.connect(host = project_config["host"],
                    port = project_config["port"], 
                    clientId = project_config["clientId"])
        
        orders = process_open_orders(ib, project_config)

        if not orders:
            return jsonify({
                'status': 'success',
                'message': 'No open orders found'
            }), 200

        # Convert dataclass list -> list of dicts
        orders_dict = [asdict(order) for order in orders]

        return jsonify({
            'status': 'success',
            'data': orders_dict
        }), 200

    except Exception as e:
        logger.error("Error fetching Alpaca orders: %s", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        ib.disconnect()
        loop.close()


@app.route("/api/place-order", methods=['POST'])
def place_order():
    data = request.json  # Get POST JSON data from Flask

    ib = IB()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Connect synchronously using the new loop
        ib.connect(
            host=project_config["host"],
            port=project_config["port"], 
            clientId=project_config["clientId"]
        )

        # --- Parse order request ---
        order = handle_place_order_request(data)  # Returns Order dataclass

        # --- Fetch executed trades ---
        executions_df = get_executed_trades(ib)
        
        # --- Determine if entry allowed ---
        entry_allowed, message = is_entry_allowed(executions_df, order.symbol, project_config)

        if not entry_allowed:
            # Entry not allowed → return JSON with message, skip order placement
            return jsonify({
                "order_placed": False,
                "entry_allowed": False,
                "message": message,
                "symbol": order.symbol
            }), 200

        # --- Proceed with order placement ---
        # Fetch latest ask price if available
        order.entry_price = get_last_ask_price(ib, order.symbol)

        # Recalculate position size
        order.position_size = calculate_position_size(
            entry_price=order.entry_price,
            stop_price=order.stop_price,
            risk=project_config["Risk"]
        )

        # Place bracket order using dataclass attributes
        parent, stoploss = place_bracket_order(
            ib=ib,
            order=order
        )

        # Return success response
        return jsonify({
            "order_placed": True,
            "entry_allowed": True,
            "message": message,
            "order": order.__dict__,  # Convert dataclass to dict
            "parent_orderId": getattr(parent, 'orderId', None),
            "stop_orderId": getattr(stoploss, 'orderId', None)
        }), 200

    except Exception as e:
        logger.error("Error placing order: %s", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        ib.disconnect()
        loop.close()

@app.route("/api/ib_accountdata", methods=['GET'])
def get_ib_data():
    ib = IB()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        ib.connect(
            host=project_config["host"],
            port=project_config["port"],
            clientId=project_config["clientId"]
        )

        # Pull data
        positions_df = get_positions(ib)
        orders_df = get_stop_orders(ib)
        account_summary = get_account_summary(ib)
        risk_levels = handle_open_risk(positions_df, orders_df,account_summary)
        #  NEW: All account summary values
        

        response = {
            "positions": positions_df.to_dict(orient="records"),
            "orders": orders_df.to_dict(orient="records"),
            "risk_levels": risk_levels.to_dict(orient="records"),
            "account_summary": account_summary
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error fetching IB account data: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        ib.disconnect()
        loop.close()
    

@app.route("/api/stoplevel", methods=['GET'])
def get_stop_level():
    """
    Fetches the stop level based on the last 10 rows from the specified table (ticker).
    :param ticker: The ticker (table name) to query.
    :return: JSON response with the stop level or an error message.
    """
    ticker = request.args.get('ticker')  # e.g., 'AAPL'
    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    stop_level = detect_stoplevel(database_config, ticker, n=10)

    if stop_level is None:
        return jsonify({"error": "Failed to calculate the stop level"}), 500

    # Convert stop level to float
    try:
        stop_level_float = float(stop_level)
    except ValueError:
        return jsonify({"error": "Invalid stop level value"}), 500

    # Return stop level as a float (calculable number)
    return jsonify({"stop_level": stop_level_float}), 200



@app.route("/api/ib_scanner", methods=['GET'])
def get_ibscanner_data():
    preset_name = request.args.get("preset")

    ib = IB()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        ib.connect(
            host=project_config["host"],
            port=project_config["port"],
            clientId=project_config["clientId"]
        )

        # Run IB scanner
        sub, df_scan = run_scanner(ib, preset_name)
        if df_scan is None or df_scan.empty:
            logger.warning(f"Scanner returned NO RESULTS for preset '{preset_name}'")
            return jsonify({"results": []})
        # Extract clean data (rank + symbol + contract dict)
        clean_data = handle_scandata_from_ib(df_scan)

        logger.info(f"Scanner returned {len(clean_data)} results for preset '{preset_name}'")

        # Fetch snapshot last prices and yesterday close
        snapshot = fetch_snapshot_prices(ib, clean_data)
        yclose   = fetch_yesterday_close(ib, clean_data)

        # Merge into results in desired order
        flat_results = []
        for item in clean_data:
            symbol = item.get("symbol")
            rank = item.get("rank")
            contract = item.get("contract")  # keep untouched

            last_price = snapshot["Symbol"].get(symbol, {}).get("last_price")
            yesterday_close = yclose["Symbol"].get(symbol, {}).get("yesterday_close")

            if last_price is not None and yesterday_close:
                change_pct = round((last_price - yesterday_close) / yesterday_close * 100, 2)
            else:
                change_pct = None

            # Build dictionary in the order you want:
            flat_item = {
                "contract": contract,
                "last_price": last_price,
                "rank": rank,
                "symbol": symbol,
                "yesterday_close": yesterday_close,
                "change_pct": change_pct
            }

            flat_results.append(flat_item)
        # Sanitize results before returning to UI
        clean_output = sanitize_for_json(flat_results)
        # Dump readable results into ib_scanner.log
        log_scan_results(preset_name, clean_output)
        logger.info(f"Final scanner results prepared with {len(clean_output)} entries.")
        return jsonify({"results": clean_output})

    except Exception as e:
        logger.exception("Error in IB scanner endpoint")
        return jsonify({"error": str(e)}), 500

    finally:
        ib.disconnect()
        loop.close()

# @app.route("/api/get_executions", methods=['GET'])
# def executions():

#     ib = IB()
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

#     try:
#         # Connect
#         ib.connect(
#             host=project_config["host"],
#             port=project_config["port"],
#             clientId=project_config["clientId"]
#         )

#         # --- Get symbol from query params or use default ---
#         symbol =  "NVDA"

#         # Fetch executed trades
#         executions_df = get_executed_trades(ib)
        
#         # --- Determine if entry allowed ---
#         entry_allowed, message = is_entry_allowed(executions_df, symbol, project_config)

#         # Convert DataFrame → list of dicts for JSON
#         executions_json = executions_df.to_dict(orient="records")

#         # --- Return full executions + entry info ---
#         return jsonify({
#             "executions": executions_json,
#             "symbol": symbol,
#             "entry_allowed": entry_allowed,
#             "message": message
#         }), 200

#     except Exception as e:
#         logger.error("Error fetching executions: %s", str(e))
#         return jsonify({"error": str(e)}), 500

#     finally:
#         ib.disconnect()
#         loop.close()




# Run Flask and IB API simultaneously
if __name__ == "__main__":
    # Serve the app with Waitress on all interfaces
    serve(app, host="0.0.0.0", port=8080)
    # Run Flask app (use built-in dev server for development)
    #app.run(host="0.0.0.0", port=8080, debug=True)