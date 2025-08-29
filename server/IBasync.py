from ib_insync import *

# Tämän koodin tarkoitus ei ole mikään muu kuin suorittaa order execution. Laskennat ja muu logiikka pitää
# hoitaa muualla. Tämä tekee kaksi orderia lmt ja stp


def get_last_ask_price(
    ib: IB,
    symbol: str,
    exchange: str = "SMART",
    currency: str = "USD",
    wait_time: int = 0.5
) -> float:
    """
    Fetches the last ask price for a given symbol from IB.

    Args:
        ib (IB): Active IB connection.
        symbol (str): Stock ticker symbol (e.g. "AAPL").
        exchange (str): Exchange to query (default SMART).
        currency (str): Currency (default USD).
        wait_time (int): Seconds to wait for market data to arrive.

    Returns:
        float: Last ask price, or None if unavailable.
    """
    try:
        # Define and qualify contract
        contract = Stock(symbol=symbol, exchange=exchange, currency=currency)
        ib.qualifyContracts(contract)

        # Request market data
        ticker = ib.reqMktData(contract, "", False, False)

        # Wait for IB to respond
        ib.sleep(wait_time)

        ask_price = ticker.ask
        if ask_price is None:
            print(f"Warning: No ask price available for {symbol}")
        else:
            print(f"{symbol} last ask price: {ask_price}")

        return ask_price

    except Exception as e:
        print(f"Error fetching last ask price for {symbol}: {e}")
        return None


def place_bracket_order(
    ib: IB,
    symbol: str,
    action: str,
    quantity: int,
    limit_price: float,
    stop_price: float,
    exchange: str = 'SMART',
    currency: str = 'USD'
):
    """
    Places a bracket order with a parent limit order and a stop loss.
    Returns the parent and stoploss orders, or (None, None) if failed.
    """
    try:
        # qualify contract
        contract = Stock(symbol=symbol, exchange=exchange, currency=currency)
        ib.qualifyContracts(contract)

        # determine reverse action
        reverse_action = 'SELL' if action.upper() == 'BUY' else 'BUY'

        # parent limit order
        parent = LimitOrder(
            action=action,
            totalQuantity=quantity,
            lmtPrice=limit_price,
            orderId=ib.client.getReqId(),
            transmit=False,
            outsideRth=True,
        )

        # stop loss order
        stoploss = StopOrder(
            action=reverse_action,
            totalQuantity=quantity,
            stopPrice=stop_price,
            orderId=ib.client.getReqId(),
            parentId=parent.orderId,
            transmit=True,  # last order in chain transmits
            outsideRth=True,
        )

        # place orders
        for order in [parent, stoploss]:
            try:
                print(f"Going live with: {order}")
                ib.placeOrder(contract, order)
                ib.sleep(0.1)  # small delay helps IB handle sequencing
            except Exception as e:
                print(f"Error placing order {order}: {e}")
                return None, None

        return parent, stoploss

    except Exception as e:
        print(f"Error in place_bracket_order for {symbol}: {e}")
        return None, None






# if __name__ == "__main__":
#     symbol = "BMNR"
#     exchange = "SMART"
#     currency = "USD"

#     ib = IB()
#     ib.connect('127.0.0.1', 7497, clientId=1)

#     # Define the contract
#     contract = Stock(symbol, exchange, currency)
#     ib.qualifyContracts(contract)
#     # Request market data
#     ticker = ib.reqMktData(contract, "", False, False)

#     # Wait until data arrives
#     ib.sleep(0.5)

#     ask_price = ticker.ask
#     print(f"{symbol} last ask price: {ask_price}")

#     ib.disconnect()
