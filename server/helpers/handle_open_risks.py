import pandas as pd


def handle_open_risk(positions_df: pd.DataFrame, 
                     orders_df: pd.DataFrame,
                     account_data: dict) -> pd.DataFrame:
    """
    Build risk table for each position:
      - OpenRisk (based on stop)
      - NetLiquidity% exposure
      - Size (absolute position value)
    """

    # Extract net liquidation from account summary
    netliq = float(account_data.get("NetLiquidation", 0))

    risk_df = pd.DataFrame(columns=[
        "Symbol",
        "Allocation",
        "Size",
        "AvgCost",
        "AuxPrice",
        "Position",
        "OpenRisk"
    ])

    row_index = 0

    for _, pos in positions_df.iterrows():
        symbol = pos["Symbol"]
        position = float(pos["Position"])
        avgcost = float(pos["AvgCost"])

        # Size = abs(position * avgcost)
        size = round(abs(position * avgcost), 2)

        # Calculate NetLiquidity% using Size
        if netliq > 0:
            netliq_pct = round((size / netliq) * 100, 2)
        else:
            netliq_pct = None

        # Find stop for this symbol
        stop_order = orders_df[
            (orders_df["Symbol"] == symbol) &
            (orders_df["OrderType"] == "STP")
        ].head(1)

        if not stop_order.empty:
            aux_price = float(stop_order.iloc[0]["AuxPrice"])
            open_risk = round(abs(position * (aux_price - avgcost)), 2)
        else:
            aux_price = None
            open_risk = None

        risk_df.loc[row_index] = {
            "Symbol": symbol,
            "Allocation": netliq_pct,
            "Size": size,
            "AvgCost": avgcost,
            "AuxPrice": aux_price,
            "Position": position,
            "OpenRisk": open_risk
        }

        row_index += 1

    return risk_df
