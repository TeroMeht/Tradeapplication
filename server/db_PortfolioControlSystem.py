import requests
import pandas as pd
import traceback
from datetime import datetime
from datetime import datetime, timezone
from decimal import Decimal

# Tää palauttaa IB portfolion tiedot
def get_ibdata(base_url="http://127.0.0.1:8080"):
   
    url = f"{base_url}/api/ib_portfoliodata"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            executions_df = pd.DataFrame(data.get("executions", []))
            orders_df = pd.DataFrame(data.get("orders", []))
            positions_df = pd.DataFrame(data.get("positions", []))

            return executions_df, orders_df, positions_df

        else:
            print(f"Failed to reach endpoint: {response.status_code}")
            return None, None, None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None, None, None



def handle_executiondata_to_aggregate(executions_df):


    # Print the capitalized column names for each DataFrame

    # Ensure numeric columns are treated correctly
    df = executions_df.copy()
    df["Shares"] = df["Shares"].astype(float)
    df["Price"] = df["Price"].astype(float)
    df["Commission"] = df["Commission"].astype(float)

    # Compute AdjustedAvgPrice per row
    df["CommissionPerShare"] = df["Commission"] / df["Shares"]
    df["AdjustedAvgPrice"] = df["Price"] + df["CommissionPerShare"]

    # Compute weighted prices
    df["WeightedPrice"] = df["Price"] * df["Shares"]
    df["WeightedAdjustedPrice"] = df["AdjustedAvgPrice"] * df["Shares"]

    # Group and aggregate
    aggregated = df.groupby("PermId").agg({
        "Symbol": "first",
        "Side": "first",
        "Shares": "sum",
        "WeightedPrice": "sum",
        "WeightedAdjustedPrice": "sum",
        "Commission": "sum",
        "Time": "min"
    }).reset_index()

    # Finalize weighted averages
    aggregated["AvgPrice"] = aggregated["WeightedPrice"] / aggregated["Shares"]
    aggregated["AdjustedAvgPrice"] = aggregated["WeightedAdjustedPrice"] / aggregated["Shares"]

    # Round for presentation
    aggregated["AvgPrice"] = aggregated["AvgPrice"].round(4)
    aggregated["AdjustedAvgPrice"] = aggregated["AdjustedAvgPrice"].round(4)
    aggregated["TotalCommission"] = aggregated["Commission"].round(4)

    # Clean up
    return aggregated[[
        "PermId", "Symbol", "Side", "Shares", "AvgPrice",
        "AdjustedAvgPrice", "TotalCommission", "Time"
    ]]



# Groupping tarvii tehdä jossain muualla tää on liian monimutkainen tyyli. Aggregate data tarvitaan kantaan jotta sitä voidaan käyttää
# fiksummin. Tarvii käsitellä ennen kuin kirjotetaan.
def insert_aggregated_execution_to_db(cursor, execution_data):
    try:
        # Use PermId as a unique identifier in this context
        check_query = """
            SELECT COUNT(*) FROM executions WHERE "PermId" = %s;
        """
        cursor.execute(check_query, (execution_data["PermId"],))
        result = cursor.fetchone()

        if result[0] > 0:
            print(f"⚠️ Aggregated execution with PermId {execution_data['PermId']} already exists.")
            return

        # Updated insert query with proper column names matching the new schema
        insert_query = """
            INSERT INTO executions (
                "Symbol", "Time", "PermId", "AvgPrice", "Shares", 
                "Side", "Commission", "AdjustedAvgPrice"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        # Prepare the values based on the provided data and correct column names
        execution_values = (
            execution_data["Symbol"],
            execution_data["Time"],
            execution_data["PermId"],
            float(execution_data["AvgPrice"]),
            int(execution_data["Shares"]),
            execution_data["Side"],
            float(execution_data["TotalCommission"]),
            float(execution_data["AdjustedAvgPrice"])
        )

        cursor.execute(insert_query, execution_values)
        print(f"✅ Inserted aggregated execution for PermId {execution_data['PermId']}")

    except Exception as e:
        print(f"❌ Error inserting aggregated execution: {e}")
        cursor.connection.rollback()





def detect_inf_risk_positions(positions_df, orders_df):
    """
    Returns a list of symbols that are in positions_df but have no corresponding entry in orders_df.
    """
    if orders_df.empty or "Symbol" not in orders_df.columns:
        order_symbols = set()
    else:
        order_symbols = set(orders_df["Symbol"])

    if "Symbol" not in positions_df.columns:
        return []

    risky_symbols = []

    for _, pos in positions_df.iterrows():
        symbol = pos.get("Symbol")
        if symbol == "IBKR":
            continue
        if symbol not in order_symbols:
            risky_symbols.append(symbol)

    return risky_symbols


def detect_adding_to_loser_positions(positions_df, executions_df):
    """
    For each symbol in positions_df, checks if there are BOT executions 
    at a lower Adjusted Avg Price than the one that opened the position.

    Returns positions_df with 'AddingToLoser' column.
    """
    positions_df = positions_df.copy()
    executions_df = executions_df.copy()

    # Ensure proper types
    executions_df['AdjustedAvgPrice'] = executions_df['AdjustedAvgPrice'].astype(float)
    executions_df['OpensPosition'] = executions_df['OpensPosition'].astype(bool)
    positions_df['AvgCost'] = positions_df['AvgCost'].astype(float)

    # Filter only BOT side executions
    bot_execs = executions_df[executions_df['Side'] == 'BOT']

    # Add result column
    positions_df['AddingToLoser'] = False

    for i, pos_row in positions_df.iterrows():
        symbol = pos_row['Symbol']

        symbol_execs = bot_execs[bot_execs['Symbol'] == symbol]


        # Find the OpensPosition execution for this symbol
        initial_execs = symbol_execs[symbol_execs['OpensPosition'] == True]


        # Assume the first one chronologically is the open
        initial_exec = initial_execs.sort_values(by='Time').iloc[0]
        initial_price = initial_exec['AdjustedAvgPrice']
        print(f"🔍 {symbol}: Initial Adjusted Avg Price = {initial_price}")

        for _, exec_row in symbol_execs.iterrows():
            exec_price = exec_row['AdjustedAvgPrice']
            exec_time = exec_row['Time']

            if exec_price < initial_price:
                print(f"   🚨 Adding to loser at {exec_time}: {exec_price} < {initial_price}")
                positions_df.at[i, 'AddingToLoser'] = True
                break
        else:
            print(f"   ✅ No losing add detected for {symbol}.")

    return positions_df

def mark_opening_executions(cursor, positions_df, executions_df):

    # Initialize OpensPosition as False
    executions_df['OpensPosition'] = False

    for _, position in positions_df.iterrows():
        symbol = position["Symbol"]
        pos_shares = Decimal(str(position["Position"]))
        pos_avg_price = Decimal(str(position["AvgCost"])).quantize(Decimal('0.01'))  # 2 decimal places
        side = "BOT" if pos_shares > 0 else "SLD"

        print(f"\n🔎 Checking Position: Symbol={symbol}, Shares={pos_shares}, AvgCost={pos_avg_price}, Side={side}")

        # Filter relevant executions and reset index to keep track of original indices
        relevant_execs = executions_df[
            (executions_df["Symbol"] == symbol) & (executions_df["Side"] == side)
        ].sort_values(by="Time").reset_index()

        matched = False
        for _, exec_row in relevant_execs.iterrows():
            exec_shares = Decimal(str(exec_row["Shares"]))
            exec_price = Decimal(str(exec_row["AdjustedAvgPrice"])).quantize(Decimal('0.01'))

            print(f"   Trying Execution: PermId={exec_row['PermId']}, Shares={exec_shares}, AdjustedAvgPrice={exec_price}")

            if exec_shares == abs(pos_shares) and exec_price == pos_avg_price:
                print(f"✅ Matched! Marking execution PermId={exec_row['PermId']} as OpensPosition")

                # Use original index to update the main executions_df
                executions_df.loc[exec_row["index"], "OpensPosition"] = True

                # Update in database
                perm_id = exec_row["PermId"]
                update_query = """
                    UPDATE executions
                    SET "OpensPosition" = TRUE
                    WHERE "PermId" = %s;
                """
                cursor.execute(update_query, (perm_id,))
                matched = True
                break  # Found the match — move to next position

        if not matched:
            print(f"❌ No match found for position: {symbol}")

    return executions_df




# Tätä kutsutaan kun logiikka napsahtaa siihen haaraan jossa alarm triggeröityy
def create_pcs_alarm(cursor, message: str, status: str = "active"):
    """
    Inserts a new alarm into the pcs_alarms table only if no active alarm with the same message exists.
    The Date will be generated automatically by the database.
    """
    try:
        # Step 1: Check if an active alarm with the same message already exists
        check_query = """
            SELECT COUNT(*) FROM pcs_alarms
            WHERE "Message" = %s AND "Status" = %s;
        """
        cursor.execute(check_query, (message, "active"))
        result = cursor.fetchone()

        # If the result is greater than 0, an active alarm with the same message already exists
        if result[0] > 0:
            print(f"⚠️ Alarm with the message '{message}' already exists and is active. No new alarm added.")
            return

        # Step 2: Insert the new alarm if no active alarm exists
        insert_query = """
            INSERT INTO pcs_alarms ("Message", "Status")
            VALUES (%s, %s);
        """
        cursor.execute(insert_query, (message, status))
        print(f"✅ Alarm created: {message}")

        # Commit the transaction if using manual commit mode
        if cursor.connection:
            cursor.connection.commit()

    except Exception as e:
        print(f"❌ Failed to insert PCS alarm: {e}")
        traceback.print_exc()





def pcs_handler(cursor):

    # Step 1: Get the data from the API
    executions_df, orders_df, positions_df = get_ibdata()
    # Print full executions_df and its columns
    print("\n📄 Executions DataFrame:")
    print(executions_df)

    # Print orders_df and its columns
    print("\n📄 Orders DataFrame:")
    print(orders_df)

    # Print positions_df and its columns
    print("\n📄 Positions DataFrame:")
    print(positions_df)

    # Handle and print aggregated data
    aggregated_df = handle_executiondata_to_aggregate(executions_df)

    print("\n📊 Aggregated Executions DataFrame:")
    print(aggregated_df)


    # Step 2: Check if executions_df is not empty. Add executions to database. Tästä tarvitaan myös historiadatat joten
    # ne voi ottaa tästä samasta streamista
    if aggregated_df is not None and not aggregated_df.empty:
       
        for _, row in aggregated_df.iterrows():
            aggregated_df = row.to_dict()  # Convert row to dictionary
            insert_aggregated_execution_to_db(cursor, aggregated_df) # Tää kirjoittaa raw execution dataa
    else:
        print("No execution data to insert.")






    # Step 3: Detect positions without matching orders
    # if positions_df is not None and not positions_df.empty:
    #     risky_symbols = detect_inf_risk_positions(positions_df, orders_df)

    #     if risky_symbols:
    #         print("⚠️ Risky positions without matching orders detected:")
    #         for sym in risky_symbols:
    #             print(f" - {sym}")

    #         message = f"Position without stop: {', '.join(risky_symbols)}🚨"
    #         create_pcs_alarm(cursor, message)
    #     else:
    #         print("✅ All positions have corresponding orders.")


    # Step 4: Check for BOT (Buy) executions with lower avg_price than position avg_cost

    executions_df= mark_opening_executions(cursor,positions_df,executions_df)



        # Run detection
        # execution_alert_df = detect_adding_to_loser_positions(positions_df, executions_df)
        # print(execution_alert_df)

        # # Check for any alert
        # if execution_alert_df["AddingToLoser"].any():
        #     # Get all symbols with violation
        #     losers = execution_alert_df[execution_alert_df["AddingToLoser"] == True]["Symbol"].tolist()
        #     for symbol in losers:
        #         msg = f"Adding to loser detected for {symbol} 🚨"
        #         create_pcs_alarm(cursor, msg)
        # else:
        #     print("✅ No losing adds detected.")



