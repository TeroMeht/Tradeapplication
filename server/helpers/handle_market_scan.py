from helpers.handle_dataframes import *
import logging
from ib_insync import *
import pandas as pd

logger = logging.getLogger(__name__)

def handle_scandata_from_ib(df_scan: pd.DataFrame) -> list:
    """
    From IB Scanner DataFrame extract:
        - rank
        - symbol
        - contract (raw dict form if possible)
    Ensures JSON-serializable output.
    """
    results = []

    for _, row in df_scan.iterrows():
        details = row.get("contractDetails")
        contract = None

        # extract contract blob
        if isinstance(details, dict):
            contract = details.get("contract")
        elif details:
            contract = getattr(details, "contract", None)

        # normalize contract for JSON (convert to dict if it has __dict__)
        if hasattr(contract, "__dict__"):
            contract = contract.__dict__

        # extract symbol
        if isinstance(contract, dict):
            symbol = contract.get("symbol", "")
        else:
            symbol = getattr(contract, "symbol", "") if contract else ""

        # extract rank
        rank = row.get("rank")
        try:
            rank = int(rank) if rank is not None else None
        except Exception:
            rank = None

        results.append({
            "symbol": str(symbol) if symbol else "",
            "rank": rank,
            "contract": contract if isinstance(contract, dict) else None
        })

    return results




def contract_from_dict(d: dict) -> Contract:
    """Convert a raw contract dict back into an ib_insync Contract object."""
    c = Contract()
    for k, v in d.items():
        # ib_insync Contract supports direct attribute assignment
        setattr(c, k, v)
    return c


def fetch_snapshot_prices(ib: IB, results: list) -> dict:
    """
    Returns:
    {
      "Symbol": {
        "SYM": { "last_price": ... }
      }
    }
    """
    tickers_raw = {}
    output = {"Symbol": {}}

    for item in results:
        cdict = item.get("contract")
        symbol = item.get("symbol", "")

        if not cdict or not symbol:
            continue

        contract = contract_from_dict(cdict)

        ticker = ib.reqMktData(
            contract=contract,
            genericTickList="",
            snapshot=True,
            regulatorySnapshot=False
        )

        tickers_raw[symbol] = (contract, ticker)

    ib.sleep(2)

    for symbol, (contract, ticker) in tickers_raw.items():
        last_price = getattr(ticker, "last", None)
        output["Symbol"][symbol] = {"last_price": last_price}

    return output

def fetch_yesterday_close(ib: IB, results: list) -> dict:
    """
    Returns:
    {
      "Symbol": {
        "SYM": { "yesterday_close": ... }
      }
    }
    """
    output = {"Symbol": {}}

    for item in results:
        cdict = item.get("contract")
        symbol = item.get("symbol", "")

        if not cdict or not symbol:
            continue

        contract = contract_from_dict(cdict)

        bars = ib.reqHistoricalData(
            contract=contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True
        )

        if bars:
            yclose = bars[0].close
        else:
            yclose = None

        output["Symbol"][symbol] = {"yesterday_close": yclose}

    return output


# --- Historical fetch intraday until this moment---
def fetch_intraday_history(ib: IB, symbol: str, time_zone: str):
    logging.info(f"Requesting intraday data for {symbol}")

    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)

    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="1 D",
        barSizeSetting="2 mins",
        whatToShow="TRADES",
        useRTH=False
    )

    if not bars:
        logging.warning(f"No historical data returned for {symbol}")
        return None
    
    # Process bars directly using the intraday handler
    processed_df = handle_incoming_dataframe_intraday(bars, symbol,time_zone)

    return processed_df
        
# --- Historical fetch for Rvol calculation ---
def fetch_intraday_volume_history(ib: IB, symbol: str, time_zone: str):
    logging.info(f"Requesting Rvol data for {symbol}")

    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)

    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="5 D",
        barSizeSetting="2 mins",
        whatToShow="TRADES",
        useRTH=False
    )

    if not bars:
        logging.warning(f"No 5-day historical data returned for {symbol}")
        return None
    
    # Process bars directly using the intraday handler
    processed_df = handle_incoming_dataframe_intradays_volume(bars, symbol,time_zone)

    return processed_df

