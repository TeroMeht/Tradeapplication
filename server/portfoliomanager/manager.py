import logging
import pandas as pd
from ib_insync import IB
from ibclient import get_positions, get_stop_orders, close_position

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Handles positions and orders for a portfolio symbol.
    Decides if a close order should be placed based on positions and open orders.
    """

    def __init__(self, ib: IB):
        self.ib = ib

    # ----------------------------
    # PUBLIC METHOD
    # ----------------------------
    def handle_automated_exit(self, symbol: str) -> str:
        """
        High-level method to process a symbol: check positions, orders, close if needed.
        """
        positions_df = self.get_positions()
        open_orders_df = self.get_open_orders()

        if self.has_existing_market_order(symbol, open_orders_df):
            return "existing_mkt_order"

        if not self.has_position(symbol, positions_df):
            return "no_position"

        qty, action = self.get_position_info(symbol, positions_df)
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
        logger.info(f"Closing position: Symbol={symbol} Action={action} Qty={quantity}")
        close_position(
            ib=self.ib,
            symbol=symbol,
            quantity=abs(quantity),
            action=action
        )