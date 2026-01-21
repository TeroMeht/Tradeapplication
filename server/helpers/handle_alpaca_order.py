from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)

from ibclient import get_last_ask_price
from common.calculate import calculate_position_size

@dataclass
class Order:
    id:str
    symbol: str
    stop_price: float
    latest_price: float = 0.0   # default 0.0, will be updated from IB
    position_size: int = 0       # default 0, calculated later


def handle_orders_data(open_orders: list, ib, project_config: dict) -> List[Order]:
    """
    Process Alpaca + DB orders: fetch latest prices and calculate position sizes.
    """
    processed_orders: List[Order] = []

    for order in open_orders:
        try:
            raw_id = order.get("id") or order.get("Id")
            symbol = order.get("symbol") or order.get("Symbol")

            if not symbol or not raw_id:
                continue

            # --- Normalize ID ---
            if isinstance(raw_id, str) and "-" in raw_id:
                order_id = raw_id.split("-")[0]   # Alpaca UUID → short ID
            else:
                order_id = str(raw_id)             # DB numeric → string-safe

            limit_price = float(order.get("limit_price") or 0.0)
            stop_price = float(order.get("stop_price") or order.get("Stop") or 0.0)

            effective_stop = stop_price or limit_price
            if effective_stop <= 0:
                continue

            latest_price = float(get_last_ask_price(ib, symbol) or 0.0)
            if latest_price <= 0:
                continue

            position_size = calculate_position_size(
                latest_price,
                effective_stop,
                project_config["Risk"]
            )

            processed_order = Order(
                id=order_id,
                symbol=symbol,
                stop_price=effective_stop,
                latest_price=latest_price,
                position_size=position_size
            )

            processed_orders.append(processed_order)

            logger.info(
                "Processed %s | ID: %s | Stop: %.2f | Last: %.2f | Pos: %d",
                symbol,
                order_id,
                effective_stop,
                latest_price,
                position_size
            )

        except Exception as e:
            logger.error(
                "Error processing order %s: %s",
                order.get("symbol") or order.get("Symbol"),
                e
            )
            continue

    return processed_orders