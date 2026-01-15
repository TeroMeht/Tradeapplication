from ib_insync import *
import pandas as pd
import time
import logging
import pytz
from datetime import datetime

logger = logging.getLogger(__name__)

ESSENTIAL_ACCOUNT_FIELDS = {
    "NetLiquidation",
    "GrossPositionValue",
    "InitMarginReq",
    "MaintMarginReq",
    "AvailableFunds",
    "ExcessLiquidity",
}

def get_last_ask_price(ib: IB, symbol: str) -> float:

    try:
        # Define and qualify contract
        contract = Stock(symbol=symbol, exchange="SMART", currency="USD")
        ib.qualifyContracts(contract)

        # Request market data
        ticker = ib.reqMktData(contract, "", False, False)

        # Wait for IB to respond
        ib.sleep(1)

        ask_price = ticker.ask
        if ask_price is None:
            logging.warning(f"Warning: No ask price available for {symbol}")
        else:
            logging.info(f"{symbol} last ask price: {ask_price}")

        return ask_price

    except Exception as e:
        logging.error(f"Error fetching last ask price for {symbol}: {e}")
        return None


def place_bracket_order(ib: IB, order:Order)-> None:
    """
    Places a bracket order with a parent limit order and a stop loss.
    Returns the parent and stoploss orders, or (None, None) if failed.
    """
    try:
        # qualify contract
        contract = Stock(symbol=order.symbol, exchange='SMART', currency='USD')
        ib.qualifyContracts(contract)

        # determine reverse action
        reverse_action = 'SELL' if order.action.upper() == 'BUY' else 'BUY'

        # parent limit order
        parent = LimitOrder(
            action=order.action,
            totalQuantity=order.position_size,
            lmtPrice=order.entry_price,
            orderId=ib.client.getReqId(),
            transmit=False,
        )

        # stop loss order
        stoploss = StopOrder(
            action=reverse_action,
            totalQuantity=order.position_size,
            stopPrice=order.stop_price,
            orderId=ib.client.getReqId(),
            parentId=parent.orderId,
            transmit=True,  # last order in chain transmits
            outsideRth=True,
        )

        # place orders
        for order in [parent, stoploss]:
            try:
                logging.info(f"Going live with: {order}")
                ib.placeOrder(contract, order)
                ib.sleep(0.1)  # small delay helps IB handle sequencing
            except Exception as e:
                logging.error(f"Error placing order {order}: {e}")
                return None, None

        return parent, stoploss

    except Exception as e:
        print(f"Error in place_bracket_order for {order.symbol}: {e}")
        return None, None


def get_stop_orders(ib: IB) -> pd.DataFrame:
    """
    Fetch all open orders and return as a DataFrame.
    """
    try:
        # Request all open orders (returns list of Trade objects)
        trades = ib.reqAllOpenOrders()
        ib.sleep(1)  # small delay to ensure IB has processed the orders

        # Convert to DataFrame
        orders_df = pd.DataFrame([{
            "OrderId": t.order.permId if t.order else None,
            "Symbol": t.contract.symbol if t.contract else None,
            "Action": t.order.action if t.order else None,
            "OrderType": t.order.orderType if t.order else None,
            "TotalQty": t.order.totalQuantity if t.order else None,
            "LmtPrice": getattr(t.order, "lmtPrice", None) if t.order else None,
            "AuxPrice": getattr(t.order, "auxPrice", None) if t.order else None,
            "Status": t.orderStatus.status if t.orderStatus else None,
            "Filled": t.orderStatus.filled if t.orderStatus else None,
            "Remaining": t.orderStatus.remaining if t.orderStatus else None
        } for t in trades])

        logging.info(f"Fetched {orders_df}")
        return orders_df

    except Exception as e:
        logging.error(f"Error fetching open orders: {e}")
        return pd.DataFrame()


def get_positions(ib: IB) -> pd.DataFrame:
    """
    Fetch all positions and return as a DataFrame.
    """
    try:
        positions = ib.reqPositions()  # returns list of ib_insync Position objects
        time.sleep(1)  # wait to ensure all data is fetched
        # Convert to DataFrame
        positions_df = pd.DataFrame([{
            "Account": p.account,
            "Symbol": p.contract.symbol if p.contract else None,
            "SecType": p.contract.secType if p.contract else None,
            "Currency": p.contract.currency if p.contract else None,
            "Position": p.position,
            "AvgCost": p.avgCost
        } for p in positions if p.position != 0])  # only non-zero positions

        logging.info(f"Fetched {positions_df}")
        return positions_df

    except Exception as e:
        logging.error(f"Error fetching positions: {e}")
        return pd.DataFrame()
    

def get_account_summary(ib: IB) -> dict:
    """
    Return only the essential IB account fields needed for calculations.
    """
    try:
        summary = ib.accountSummary()
        filtered = {}

        for item in summary:
            if item.tag in ESSENTIAL_ACCOUNT_FIELDS:
                # Convert numeric fields to float safely
                try:
                    filtered[item.tag] = float(item.value)
                except:
                    filtered[item.tag] = item.value

        return filtered

    except Exception as e:
        logging.error(f"Error fetching essential account summary: {e}")
        return {}
    

def get_executed_trades(ib: IB) -> pd.DataFrame:
    """
    Fetch all executed trades (completed fills) from IB and return as a DataFrame.
    Converts execution time to Helsinki timezone.
    """
    try:
        helsinki_tz = pytz.timezone("Europe/Helsinki")
        trades = ib.trades()
        ib.sleep(1)

        executed = []

        for t in trades:
            if not t.fills:
                continue

            for fill in t.fills:

                # Convert IB timestamp (UTC) → Helsinki
                time_utc = fill.execution.time  # datetime in UTC

                # Convert
                time_helsinki = time_utc.astimezone(helsinki_tz)

                executed.append({
                    "TradeId": t.order.permId if t.order else None,
                    "Symbol": t.contract.symbol if t.contract else None,
                    "SecType": t.contract.secType if t.contract else None,
                    "Action": fill.execution.side if fill.execution else None,
                    "Quantity": fill.execution.shares if fill.execution else None,
                    "Price": fill.execution.price if fill.execution else None,    # keep original
                    "Time": time_helsinki.isoformat(),  # converted
                    "Exchange": fill.execution.exchange if fill.execution else None,
                    "Commission": (
                        fill.commissionReport.commission
                        if fill.commissionReport else None
                    ),
                })

        trades_df = pd.DataFrame(executed)
        logging.info(f"Fetched executed trades: {len(trades_df)}")

        return trades_df

    except Exception as e:
        logging.error(f"Error fetching executed trades: {e}")
        return pd.DataFrame()



def close_position(ib: IB, symbol: str, quantity: int, action: str) -> None:
    """
    Send a market order to close a position.

    :param ib: Connected IB instance
    :param symbol: Stock symbol (e.g. "AAPL")
    :param quantity: Number of shares to close
    :param action: "SELL" or "BUY"
    """
    try:
        contract = Stock(symbol=symbol, exchange="SMART", currency="USD")
        ib.qualifyContracts(contract)

        order = MarketOrder(
            action=action,
            totalQuantity=quantity,
            outsideRth=True
        )

        ib.placeOrder(contract, order)
        ib.sleep(0.2)

        logging.info(
            f"Sent {action} market order to close "
            f"{quantity} shares of {symbol}"
        )

    except Exception as e:
        logging.error(f"Error closing position for {symbol}: {e}")