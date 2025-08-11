
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
        self.executions = pd.DataFrame(columns=[
                            "Symbol", "ExecId", "Time", "Price", "PermId", "AvgPrice", "Shares", "Side"
                        ])

        self.commissions = pd.DataFrame()


    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        # Check if the errorCode is in the list of codes to skip
        if errorCode in [2104, 2106, 2158, 2176]:
            return  # Skip printing for these error codes
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def nextValidId(self, orderId: int) -> None:

        super().nextValidId(orderId)
        print(f"Connected: Next Valid Order ID is {orderId}")
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
    
    def place_order(self, contract: Contract, action: str, quantity: int, price: float, stop_price: float, ordertype) -> None:
        
        
        order = Order()
        order.orderId = self.nextOrderId
        print(order.orderId)
        order.orderType = ordertype
        print(order.orderType)
        order.lmtPrice = price
        order.action = action
        print(order.action)      
        order.totalQuantity = quantity
        print(order.totalQuantity)
        order.transmit = False
        order.eTradeOnly = ''
        order.firmQuoteOnly = ''

        

        stop_order = Order()
        stop_order.orderId = order.orderId + 1
        print(stop_order.orderId)
        stop_order.parentId = order.orderId
        print(stop_order.parentId)  # Ensure stop order has a unique ID
        stop_order.orderType = 'STP'
        stop_order.auxPrice = stop_price
        stop_order.action = 'SELL'
        stop_order.totalQuantity = quantity
        stop_order.transmit = True



        stop_order.eTradeOnly = ''
        stop_order.firmQuoteOnly = ''

        # Place the order
        self.placeOrder(order.orderId, contract, order)
        self.placeOrder(stop_order.orderId, contract, stop_order)
        # Print order summary in one line
        print(f"Order placed: Symbol={contract.symbol}, Price={price}, Quantity={quantity}")
        # Increment the next order ID


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
            barSizeSetting="1 min",
            whatToShow="TRADES",
            useRTH=0,
            formatDate=1,
            keepUpToDate=False,
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

    def get_lastPrice(self, reqId: int, contract: Contract):
        # Initialize the DataFrame for real-time bars
        self.realtimebars = pd.DataFrame(columns=[
            "TickerId", "Time", "Open", "High", "Low", "Close", "Volume", "WAP", "Count"
        ])
        
        # Request real-time bars from the IB API
        self.reqRealTimeBars(reqId, contract, 5, "MIDPOINT", False, [])
        time.sleep(1)  # Give some time to collect data

        # Check if the DataFrame is empty
        if self.realtimebars.empty:
            return None  # Handle the case where no data is received

        # Get the last row of the DataFrame
        last_row = self.realtimebars.iloc[-1]

        # Calculate the average price
        average_price = (last_row["Open"] + last_row["High"] + last_row["Low"] + last_row["Close"]) / 4
        average_price = round(average_price,2)
        return average_price

    def get_executions(self) -> pd.DataFrame:
        self.reqExecutions(10001, ExecutionFilter())  # Triggers execDetails for each execution
        time.sleep(1)  # Optional: allow some time for execDetails to populate
        return self.executions, self.commissions

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


    def commissionReport(self, commissionReport: CommissionReport):
        super().commissionReport(commissionReport)
        
        # Convert commission report to a dictionary
        report_dict = {
            "ExecId": commissionReport.execId,
            "Commission": commissionReport.commission,
            "Currency": commissionReport.currency,
            "RealizedPNL": commissionReport.realizedPNL,
            "Yield": commissionReport.yield_,
            "YieldRedemptionDate": commissionReport.yieldRedemptionDate,
        }

        # Append to the commissions DataFrame
        self.commissions = pd.concat([self.commissions, pd.DataFrame([report_dict])], ignore_index=True)

