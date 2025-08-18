
from ibapi.client import *
from ibapi.wrapper import *
from decimal import Decimal
from typing import Dict, Optional
import pandas as pd
import time
import threading



# IB API Client Code
class IbapiApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

        self.nextOrderId: Optional[int] = 0
        self.data: Dict[int, pd.DataFrame] = {}
        self.positions = pd.DataFrame()
        self.orders = pd.DataFrame(columns=[
            'OrderId','Symbol', 'Action', 'OrderType', 'TotalQty', 'LmtPrice','AuxPrice'
        ])
        self.realtimebars = pd.DataFrame()
        self.connected_flag = threading.Event()
        self.accountdata = pd.DataFrame()


    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        # Check if the errorCode is in the list of codes to skip
        if errorCode in [2104, 2106, 2158, 2176]:
            return  # Skip printing for these error codes
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def nextValidId(self, orderId: int) -> None:

        super().nextValidId(orderId)
        self.connected_flag.set()
        self.nextOrderId = orderId




    @staticmethod
    def get_contract(symbol: str) -> Contract:

        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "ARCA"
        return contract
    

    def place_order(self, contract, action, quantity, price, stop_price, ordertype):
        # Parent
        parent = Order()
        parent.orderId = self.nextOrderId
        parent.action = action
        parent.orderType = ordertype
        parent.lmtPrice = price
        parent.totalQuantity = quantity
        parent.transmit = False
        parent.eTradeOnly = ''
        parent.firmQuoteOnly = ''

        # Stop-loss
        stop_order = Order()
        stop_order.orderId = parent.orderId + 1
        stop_order.parentId = parent.orderId
        stop_order.orderType = 'STP'
        stop_order.auxPrice = stop_price
        stop_order.action = 'SELL' if action == 'BUY' else 'BUY'
        stop_order.totalQuantity = quantity
        stop_order.transmit = True  # last in chain
        stop_order.eTradeOnly = ''
        stop_order.firmQuoteOnly = ''


        # Place together
        self.placeOrder(parent.orderId, contract, parent)
        time.sleep(0.5)  # Ensure parent order is processed before placing stop order
        self.placeOrder(stop_order.orderId, contract, stop_order)

        self.nextOrderId += 2


    # def orderStatus(self, orderId: OrderId, status: str, filled: Decimal, remaining: Decimal, avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
    #     print(f"orderId: {orderId}, status: {status}, filled: {filled}, remaining: {remaining}, avgFillPrice: {avgFillPrice}, permId: {permId}, parentId: {parentId}, lastFillPrice: {lastFillPrice}, clientId: {clientId}, whyHeld: {whyHeld}, mktCapPrice: {mktCapPrice}")
    
    # Force liquidate positions that you are not supposed to be involved
    def place_market_order(self, contract: Contract, action: str, quantity: int) -> None:
        """
        Force an immediate exit of a position by placing a market order.
        
        Args:
            contract (Contract): The contract representing the position to close.
            action (str): "BUY" to close a short position or "SELL" to close a long position.
            quantity (int): The number of contracts/shares to close.
        """
        try:
            # Create a market order to force the exit
            order = Order()
            order.action = action
            order.orderType = 'MKT'  # Market order to execute immediately
            order.totalQuantity = quantity
            order.transmit = True  # Ensure the order is transmitted immediately
            order.eTradeOnly = ''
            order.firmQuoteOnly = ''

            # Place the order (no need for stop order in force exit)
            self.placeOrder(self.nextOrderId, contract, order)
            print(f"Force exit order placed: Symbol={contract.symbol}, Action={action}, Quantity={quantity}")

            # Increment the next order ID
            self.nextOrderId += 1

        except Exception as e:
            print(f"Failed to force exit position. Error: {str(e)}")

    def get_historical_data(self, reqId: int, contract: Contract) -> pd.DataFrame:

        self.data[reqId] = pd.DataFrame(columns=["time", "high", "low", "close","open"])
        self.data[reqId].set_index("time", inplace=True)
        self.reqHistoricalData(
            reqId=reqId,
            contract=contract,
            endDateTime="",
            durationStr="1 D",
            barSizeSetting="5 mins",
            whatToShow="TRADES",
            useRTH=0,
            formatDate=1,
            keepUpToDate=True,
            chartOptions=[],
        )
        time.sleep(1)
        return self.data[reqId]

    def get_stopOrders(self) -> pd.DataFrame:

        self.reqAllOpenOrders()
        time.sleep(1) # tässä pitäis oikeesti odottaa vastausta että kaikki positiot on haettu

        return self.orders

    def get_positions(self) -> pd.DataFrame:
        self.positions = pd.DataFrame(columns=[
            'Account', 'Symbol', 'SecType', 'Currency', 'Position', 'AvgCost'
        ])
        self.reqPositions()
        time.sleep(1) # tässä pitäis oikeesti odottaa vastausta että kaikki positiot on haettu
        return self.positions

    def get_accountdata(self) -> pd.DataFrame:
        self.reqAccountUpdates(True, 'DU7263343')
        time.sleep(1)
        return self.accountdata


    def get_lastPrice(self, reqId: int, contract: Contract):
        # Initialize the DataFrame for real-time bars
        self.realtimebars = pd.DataFrame(columns=[
            "TickerId", "Time", "Open", "High", "Low", "Close", "Volume", "WAP", "Count"
        ])
        
        # Request real-time bars from the IB API
        print("Requesting real-time bars from IB API...")
        self.reqRealTimeBars(reqId, contract, 5, "MIDPOINT", False, [])
        time.sleep(1)  # Give some time to collect data

        # If no real-time bar data, fall back to historical data
        if self.realtimebars.empty:
            print("No real-time data received. Fetching historical data instead...")
            historical_df = self.get_historical_data(reqId, contract)
            time.sleep(1)  # Ensure historical data is ready

            if not historical_df.empty:
                last_close = historical_df.iloc[-1]["close"]
                print(f"Price fetched from historical data: {last_close}")
                return round(last_close, 2)
            print("No historical data received either.")
            return None

        # If we have real-time bar data
        last_row = self.realtimebars.iloc[-1]
        average_price = (last_row["Open"] + last_row["High"] + last_row["Low"] + last_row["Close"]) / 4
        print(f"Price fetched from real-time bars (average OHLC): {average_price}")
        return round(average_price, 2)



    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState: OrderState): 
 
        # Create a dictionary with the order data
        order_data = {
            "OrderId": order.permId,                # Unique order ID
            "Symbol": contract.symbol,         # Stock or instrument symbol
            "Action": order.action,            # Action (e.g., "BUY" or "SELL")
            "OrderType": order.orderType,      # Type of order (e.g., "LIMIT", "MARKET")
            "TotalQty": order.totalQuantity,   # Total quantity of the order
            "LmtPrice": order.lmtPrice,        # Limit price (nullable for market orders)
            "AuxPrice": order.auxPrice         # Auxiliary price (e.g., stop price)
        }
        
        self.orders.loc[len(self.orders)] = order_data
  
    def position(self, account: str, contract: Contract, position: Decimal, avgCost: float):
        
        # Only add to the DataFrame if the position is not zero
        if position != 0:
            # Create a dictionary with the position data
            position_data = {
                "Account": account,
                "Symbol": contract.symbol,
                "SecType": contract.secType,
                "Currency": contract.currency,
                "Position": position,
                "AvgCost": round(avgCost,2)
            }

            # Append the dictionary as a new row to the DataFrame
            self.positions.loc[len(self.positions)] = position_data

    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float, low: float, close: float,
                    volume: Decimal, wap: Decimal, count: int):
        # Create a dictionary with the real-time bar data
        realtime_data = {
            "TickerId": reqId,
            "Time": time,
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
            "WAP": wap,
            "Count": count
        }
        
        # Append the dictionary as a new row to the DataFrame using the approach you requested
        self.realtimebars.loc[len(self.realtimebars)] = realtime_data

    def historicalData(self, reqId: int, bar: BarData) -> None:

        # Get the DataFrame for the given request ID
        df = self.data[reqId]

        # Correctly parse the bar.date as a string into a datetime object
        # Assuming the date format is 'YYYYMMDD HH:MM:SS'
        timestamp = pd.to_datetime(bar.date, format='%Y%m%d %H:%M:%S')

        # Assign the bar data (high, low, close) to the correct timestamp in the DataFrame
        df.loc[timestamp, ["high", "low", "close","open"]] = [bar.high, bar.low, bar.close, bar.open]

        # Ensure the data is in float format for the price columns
        df = df.astype(float)
        
        # Update the DataFrame in self.data
        self.data[reqId] = df
    
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        super().execDetails(reqId, contract, execution)

        # Extract execution details
        symbol = contract.symbol
        exec_id = execution.execId
        time_str = execution.time.replace("  ", " ")  # Normalize spacing
        price = execution.price
        perm_id = execution.permId
        avg_price = execution.avgPrice
        shares = execution.shares
        side = execution.side

       # print(f"Symbol: {symbol}, ExecId: {exec_id}, Time: {time_str}, Price: {price}, PermId: {perm_id}, AvgPrice: {avg_price}, Shares: {shares}, Side: {side}")

        # Append to the DataFrame
        new_row = {
            "Symbol": symbol,
            "ExecId": exec_id,
            "Time": time_str,
            "Price": price,
            "PermId": perm_id,
            "AvgPrice": avg_price,
            "Shares": shares,
            "Side": side
        }

        self.executions.loc[len(self.executions)] = new_row

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str) -> pd.DataFrame:
        super().updateAccountValue(key, val, currency, accountName)


        # Initialize as empty DataFrame if not exists
        if not hasattr(self, "accountdata") or self.accountdata is None:
            self.accountdata = pd.DataFrame(columns=["Key", "Value", "Currency", "AccountName"])

        new_row = pd.DataFrame([{
            "Key": key,
            "Value": val,
            "Currency": currency,
            "AccountName": accountName
        }])

        self.accountdata = pd.concat([self.accountdata, new_row], ignore_index=True)

        return self.accountdata
