from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)

from ibclient import get_last_ask_price
from common.calculate import calculate_position_size

@dataclass
class AlpacaOrder:
    symbol: str
    stop_price: float
    latest_price: float = 0.0   # default 0.0, will be updated from IB
    position_size: int = 0       # default 0, calculated later


def handle_orders_data(open_orders: list, ib, project_config: dict) -> List[AlpacaOrder]:
    """Process Alpaca orders: fetch latest prices and calculate position sizes."""
    processed_orders: List[AlpacaOrder] = []

    for order in open_orders:
        try:
            symbol = order.get("symbol")
            if not symbol:
                continue  # skip invalid order

            limit_price = float(order.get("limit_price") or 0.0)
            stp_price = float(order.get("stop_price") or 0.0)
            latest_price = float(get_last_ask_price(ib, symbol) or 0.0)

            # Calculate position size based on your risk model
            stop_price= stp_price or limit_price
            position_size = calculate_position_size(latest_price, stop_price, project_config["Risk"])

            alpaca_order = AlpacaOrder(
                symbol=symbol,
                stop_price=stop_price,
                latest_price=latest_price,
                position_size=position_size
            )

            processed_orders.append(alpaca_order)
            logger.info(
                "Processed %s  | Stop: %.2f | Last: %.2f | Pos: %d",
                symbol, stop_price, latest_price, position_size
            )

        except Exception as e:
            logger.error("Error processing order %s: %s", order.get("symbol"), e)
            continue

    return processed_orders