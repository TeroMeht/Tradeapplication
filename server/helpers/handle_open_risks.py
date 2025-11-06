import pandas as pd


# Tää on alempaan tableen ja laskee riskitasoja positioille
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
