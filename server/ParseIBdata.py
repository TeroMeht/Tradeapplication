import pandas as pd

def parse_ib_data(raw_data):
    parsed = {}

    # --- STOP ORDERS ---
    orders_df = raw_data.get("orders", pd.DataFrame())
    stop_orders = []

    if not orders_df.empty:
        for _, row in orders_df.iterrows():
            order = getattr(row, "order", None)
            contract = getattr(row, "contract", None)
            status = getattr(row, "orderStatus", None)

            # Check if order exists and is a stop order
            if order and getattr(order, "orderType", None) == "STP":
                stop_orders.append({
                    "symbol": getattr(contract, "symbol", None),
                    "action": getattr(order, "action", None),
                    "totalQuantity": getattr(order, "totalQuantity", None),
                    "auxPrice": getattr(order, "auxPrice", None),
                    "trailStopPrice": getattr(order, "trailStopPrice", None),
                    "status": getattr(status, "status", None)
                })
    parsed["stopOrders"] = stop_orders

    # --- POSITIONS ---
    positions_df = raw_data.get("positions", pd.DataFrame())
    positions_list = []

    if not positions_df.empty:
        for _, row in positions_df.iterrows():
            contract = getattr(row, "contract", None)
            positions_list.append({
                "symbol": getattr(contract, "symbol", None),
                "secType": getattr(contract, "secType", None),
                "exchange": getattr(contract, "exchange", None),
                "position": getattr(row, "position", None),
                "avgCost": getattr(row, "avgCost", None),
                "currency": getattr(contract, "currency", None)
            })
    parsed["positions"] = positions_list

    # --- ACCOUNT DATA (filtered) ---
    account_df = raw_data.get("account", pd.DataFrame())
    if not account_df.empty:
        # Only include 'Currency' and 'CashBalance' for 'All' account
        filtered_account = account_df[
            (account_df["tag"].isin(["Currency", "CashBalance"]))
        ]
        parsed["account"] = filtered_account.to_dict(orient="records")
    else:
        parsed["account"] = []

    return parsed