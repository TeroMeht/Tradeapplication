import logging
import pandas as pd
from ib_insync import *
from ibclient import get_positions, get_stop_orders, close_position
from typing import List

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Handles positions and orders for a portfolio symbol.
    Decides if a close order should be placed based on positions and open orders.
    """

    def __init__(self, ib: IB):
        self.ib = ib
        self.positions_df = self.get_positions()
        self.open_orders_df = self.get_open_orders()

    # ----------------------------
    # PUBLIC METHOD
    # ----------------------------
    def handle_automated_exit(self, symbol: str) -> str:
        """
        High-level method to process a symbol: check positions, orders, close if needed.
        """
        if self.has_existing_market_order(symbol, self.open_orders_df):
            return "existing_mkt_order"

        if not self.has_position(symbol, self.positions_df):
            return "no_position"

            # 3️⃣ Fetch all trades from this session and filter by symbol
           # Cancel active trades first
        active_trades = self.active_trades_by_symbol(symbol)
        self.cancel_trades(active_trades)

        

        qty, action = self.get_position_info(symbol, self.positions_df)
        self.close_position(symbol, qty, action)

        return "closing position"

    # ----------------------------
    # INTERNAL METHODS
    # ----------------------------
    def get_positions(self) -> pd.DataFrame:
        """Fetch positions safely"""
        try:
            return get_positions(self.ib)
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return pd.DataFrame()

    def get_open_orders(self) -> pd.DataFrame:
        """Fetch open orders safely"""
        try:
            return get_stop_orders(self.ib)
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return pd.DataFrame()



    def active_trades_by_symbol(self, symbol: str) -> List[Trade]:
        try:
            trades = self.ib.trades()  # This calls IB's trades() method internally
            print(f"Trades fetched: {trades}")
            # Filter by symbol and order status
            filtered = [
                t for t in trades
                if t.contract and t.contract.symbol == symbol
                and t.orderStatus.status == "PreSubmitted"
            ]
            return filtered
        except Exception as e:
            logging.error(f"Error fetching trades in PortfolioManager: {e}")
            return []


    def has_position(self, symbol: str, positions_df: pd.DataFrame) -> bool:
        """Check if we have a position for the symbol"""
        return not positions_df.loc[positions_df["Symbol"] == symbol].empty

    def get_position_info(self, symbol: str, positions_df: pd.DataFrame) -> tuple[int, str]:
        """
        Returns quantity and action ("BUY"/"SELL") for the symbol.
        Positive quantity -> SELL to close
        Negative quantity -> BUY to close
        """
        row = positions_df.loc[positions_df["Symbol"] == symbol].iloc[0]
        qty = int(row["Position"])
        action = "SELL" if qty > 0 else "BUY"
        qty = abs(qty) # Make quantity positive for order
        return qty, action

    def has_existing_market_order(self, symbol: str, open_orders_df: pd.DataFrame) -> bool:
        """Return True if there is already an MKT order for the symbol"""
        if open_orders_df.empty:
            logger.info(f"No open orders at all for {symbol}, safe to create new close order.")
            return False

        existing_mkt_orders = open_orders_df.loc[
            (open_orders_df["Symbol"] == symbol) &
            (open_orders_df["OrderType"].str.upper() == "MKT") &
            (~open_orders_df["Status"].str.upper().isin(["CANCELLED"]))
        ]

        if not existing_mkt_orders.empty:
            logger.info(
                f"Market order already exists for {symbol}, skipping new close order:\n{existing_mkt_orders}"
            )
            return True

        return False
    

    def close_position(self, symbol: str, quantity: int, action: str) -> None:
        """Send market order to close the position"""
        close_position(
            ib=self.ib,
            symbol=symbol,
            quantity=abs(quantity),
            action=action
        )

    def cancel_trades(self, trades: List[Trade]) -> None:
        """
        Cancel a list of trades by calling the PortfolioManager's cancelOrder method.

        Args:
            trades: List of Trade objects to cancel.
        """
        if not trades:
            logger.info("cancel_trades: No trades provided to cancel.")
            return

        for trade in trades:
            if trade.order:

                self.ib.cancelOrder(trade.order)  # call your existing cancelOrder method


            else:
                logger.warning(f"Trade has no order attached: {trade}")