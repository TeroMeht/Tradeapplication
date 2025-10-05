from ib_insync import *
import pandas as pd
import asyncio

class IBClient:
    def __init__(self):
        self.ib = IB()

    def connect(self, host, port, clientId):
        # Ensure an asyncio loop exists in the current thread
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        print(" Connecting to IB...")
        self.ib.connect(host, port, clientId=clientId)


    def get_stopOrders(self) -> pd.DataFrame:
        orders = self.ib.reqOpenOrders()
        if not orders:
            orders = self.ib.reqAllOpenOrders()
        return util.df(orders) if orders else pd.DataFrame()

    def get_positions(self) -> pd.DataFrame:
        positions = self.ib.positions()
        return util.df(positions) if positions else pd.DataFrame()

    def get_accountdata(self) -> pd.DataFrame:
        account_summary = self.ib.accountSummary()
        return util.df(account_summary) if account_summary else pd.DataFrame()

    def fetch_all(self):
        try:
            return {
                "orders": self.get_stopOrders(),
                "positions": self.get_positions(),
                "account": self.get_accountdata()
            }
        except Exception as e:
            print(f" Error fetching IB data: {e}")
            return {
                "orders": pd.DataFrame(),
                "positions": pd.DataFrame(),
                "account": pd.DataFrame()
            }

    def close(self):
        if self.ib.isConnected():
            self.ib.disconnect()
            print(" Disconnected from IB")
