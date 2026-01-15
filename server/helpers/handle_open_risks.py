import pandas as pd
from dataclasses import dataclass, asdict,field
from typing import Optional


@dataclass
class PortfolioPosition:
    Symbol: str
    Allocation: Optional[float]
    Size: float
    AvgCost: float
    AuxPrice: Optional[float] = field(default=0.0)
    Position: float = 0.0
    OpenRisk: Optional[float] = field(default=0.0)



def handle_open_risk(
    positions_df: pd.DataFrame, 
    orders_df: pd.DataFrame,
    account_data: dict
) -> pd.DataFrame:
    """
    Build risk table for each position:
      - OpenRisk (based on stop)
      - NetLiquidity% exposure
      - Size (absolute position value)
    """

    netliq = float(account_data.get("NetLiquidation", 0))

    # Ensure orders_df has expected columns
    if orders_df is None or orders_df.empty:
        orders_df = pd.DataFrame(columns=["Symbol", "OrderType", "AuxPrice"])

    risk_rows = []

    for _, pos in positions_df.iterrows():
        symbol = pos["Symbol"]
        position = float(pos["Position"])
        avgcost = float(pos["AvgCost"])
        size = round(abs(position * avgcost), 2)
        allocation = round((size / netliq) * 100, 2) if netliq > 0 else None

        # Safe lookup for stop order
        stop_order = orders_df[
            (orders_df.get("Symbol", pd.Series(dtype=str)) == symbol) &
            (orders_df.get("OrderType", pd.Series(dtype=str)) == "STP")
        ].head(1)

        if not stop_order.empty:
            aux_price = float(stop_order.iloc[0]["AuxPrice"])
            open_risk = round(abs(position * (aux_price - avgcost)), 2)
        else:
            aux_price = 0.0
            open_risk = 999999999

        # Append as dataclass dict
        risk_rows.append(asdict(PortfolioPosition(
            Symbol=symbol,
            Allocation=allocation,
            Size=size,
            AvgCost=avgcost,
            AuxPrice=aux_price,
            Position=position,
            OpenRisk=open_risk
        )))

    # Create DataFrame in one shot
    risk_df = pd.DataFrame(risk_rows)


    print(risk_df)
    return risk_df
