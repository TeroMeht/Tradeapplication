from ib_insync import *
import pandas as pd
from AdjustTimezone import adjust_timezone_IB_data
import numpy as np
from datetime import datetime
util.startLoop()


def get_hot_by_volume_data(ib, numberOfRows=10, marketCapAbove=10000, abovePrice=10, aboveVolume=100000):

    # Define scanner subscription
    sub = ScannerSubscription(
        numberOfRows=numberOfRows,
        instrument='STK',
        locationCode='STK.US.MAJOR',
        scanCode="HOT_BY_VOLUME",
        marketCapAbove=marketCapAbove,
        abovePrice=abovePrice,
        aboveVolume=aboveVolume,
        stockTypeFilter='CORP'
    )

    # Request scanner data
    df_scan = ib.reqScannerData(sub)

    # Convert to DataFrame safely
    df_scan = util.df(df_scan)
    if df_scan is None or df_scan.empty:
        print("No scanner data received.")
        return {}, pd.DataFrame(columns=['rank','contractDetails','contract','symbol'])

    # Extract contract and symbol
    df_scan['contract'] = df_scan.apply(lambda l: getattr(l['contractDetails'], 'contract', None), axis=1)
    df_scan['symbol'] = df_scan.apply(lambda l: getattr(l['contract'], 'symbol', None), axis=1)

    # Filter out any missing contracts
    df_scan = df_scan.dropna(subset=['contract'])

    # Request snapshot market data for each contract
    ticker_dict = {}
    for contract in df_scan['contract'].tolist():
        ticker_dict[contract] = ib.reqMktData(contract=contract, genericTickList="", snapshot=True, regulatorySnapshot=False)

    # Wait for data to populate
    ib.sleep(2)

    return ticker_dict, df_scan


def display_stock_with_marketdata(df_scan, ticker_dict):
    # Base stock info
    df = df_scan  # should have 'rank' and 'symbol'

    # Build market data DataFrame
    market_data_list = []
    for ticker in ticker_dict.values():
        contract = ticker.contract
        market_data_list.append({
            'symbol': contract.symbol,
            'close': getattr(ticker, 'close', None),
            'last': getattr(ticker, 'last', None),
            'bid': getattr(ticker, 'bid', None),
            'ask': getattr(ticker, 'ask', None)
        })
    market_data_df = pd.DataFrame(market_data_list)

    # Merge
    df_merged = df.merge(market_data_df, on='symbol', how='left')

    # Compute % Change safely
    df_merged['% Change'] = ((df_merged['last'] - df_merged['close']) / df_merged['close'] * 100).round(2)

    # ✅ Capitalize column names after merge
    df_merged.rename(columns=lambda c: c.capitalize() if not c.startswith('%') else c, inplace=True)

    return df_merged[['Rank', 'Symbol', 'Close', 'Last', 'Bid', 'Ask', '% Change']]



def handle_incoming_dataframe_intraday(
    bars_df, 
    symbol, 
    adjust_timezone_IB_data # pass this function as well
):
    try:
        if bars_df is not None and not bars_df.empty:
            for col in ['average', 'barCount']:
                if col in bars_df.columns:
                    bars_df = bars_df.drop(columns=[col])

            if 'date' in bars_df.columns:
                bars_df['date'] = bars_df['date'].apply(adjust_timezone_IB_data)

            bars_df.columns = [col.capitalize() for col in bars_df.columns]
            bars_df['Symbol'] = symbol

            bars_df = bars_df[['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']]


            # Split Date into Date and Time
            if bars_df['Date'].dtype == object:
                bars_df[['Date', 'Time']] = bars_df['Date'].str.split(' ', expand=True)
            else:
                bars_df['Date'] = bars_df['Date'].astype(str)
                bars_df[['Date', 'Time']] = bars_df['Date'].str.split(' ', expand=True)

            data = bars_df[['Symbol', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()

            return data
        else:
            print("empty data")

    except Exception as e:
        print(f"An error occurred while processing the data: {e}")


def fetch_historydata_by_symbol(symbol, ib, days):
    """
    Fetch historical intraday data (2-min bars) for a single symbol.
    """

    # Create an IB contract
    contract = Stock(symbol, 'SMART', 'USD')
    contract.primaryExchange = 'ARCA'

    # Request historical 2-min bars
    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr=f"{days} D",
        barSizeSetting="2 mins",
        whatToShow="TRADES",
        useRTH=False,   # include premarket
        formatDate=1
    )

    if not bars:
        print(f"No historical data for {symbol}")
        return pd.DataFrame(columns=["Symbol", "Date", "Time", "Open", "High", "Low", "Close", "Volume"])

    # Convert to DataFrame
    bars_df = pd.DataFrame([bar.__dict__ for bar in bars])

    # Apply preprocessing (timezone & cleaning logic)
    processed_df = handle_incoming_dataframe_intraday(
        bars_df=bars_df,
        symbol=contract.symbol,
        adjust_timezone_IB_data=adjust_timezone_IB_data
    )

    if processed_df is None or processed_df.empty:
        print(f"No processed data for {symbol}")
        return pd.DataFrame(columns=["Symbol", "Date", "Time", "Open", "High", "Low", "Close", "Volume"])

    # Add symbol column
    processed_df["Symbol"] = symbol
    return processed_df




def fetch_history_data(df_stocks, ib, days):
    """
    Fetch 5-day historical intraday data (2-min bars) for all symbols.
    Returns a list of DataFrames, one per symbol.
    """
    day5_history_datas = []

    for symbol in df_stocks["Symbol"]:
        df_history_symbol = fetch_historydata_by_symbol(symbol, ib, days=days)
        if not df_history_symbol.empty:
            day5_history_datas.append(df_history_symbol)

    return day5_history_datas


def calculate_avg_volume(day5_history_datas):
    """
    Calculate average volume per 2-min bar for each symbol.
    Returns a list of DataFrames with columns: Symbol, Time, Avg_volume
    """
    avg_volumes = []

    for df_history_symbol in day5_history_datas:
        symbol = df_history_symbol["Symbol"].iloc[0]

        # Group by (Symbol, Time) and average only Volume
        df_avg = (
            df_history_symbol
            .groupby(["Symbol", "Time"], as_index=False)["Volume"]
            .mean()
            .rename(columns={"Volume": "Avg_volume"})
        )

        avg_volumes.append(df_avg)

        # print(f"\n===== {symbol} - Avg Volumes =====")
        # print(df_avg)

    return avg_volumes


def compare_to_avg_volume(df_new, df_avg_model):

 

    # Merge by Symbol & Time
    df_merge = pd.merge(
        df_new[["Symbol", "Time", "Volume"]],
        df_avg_model,
        on=["Symbol", "Time"],
        how="left"
    )

    # Compute relative volume (Rvol = Volume / Avg_volume)
    df_merge["Rvol"] = df_merge["Volume"] / df_merge["Avg_volume"]

    # Optional: keep only relevant columns
    Rvol_data = df_merge[["Symbol", "Time", "Volume", "Avg_volume", "Rvol"]]

    return Rvol_data


def compare_and_save_rvolumes(df_today_volumes, avg_volumes):



    all_Rvol_data = []

    for df_today in df_today_volumes:
        symbol = df_today["Symbol"].iloc[0]

        # Find matching avg volume
        df_avg = next((df for df in avg_volumes if df["Symbol"].iloc[0] == symbol), None)
        if df_avg is None:
            print(f"No avg volume data for {symbol}, skipping.")
            continue

        # Merge on Time
        df_merged = df_today.merge(df_avg[['Time', 'Avg_volume']], on='Time', how='inner')

        # Compute Rvol
        df_merged['Rvol'] = (df_merged['Volume'] / df_merged['Avg_volume']).round(2)

        # Keep relevant columns
        df_result = df_merged[['Symbol', 'Date', 'Time', 'Volume', 'Avg_volume', 'Rvol']]

        all_Rvol_data.append(df_result)

    # Combine all symbols
    if all_Rvol_data:
        Rvol_data_all = pd.concat(all_Rvol_data, ignore_index=True)
        return Rvol_data_all
    else:
        print("No Rvol data generated.")
        return pd.DataFrame()




def round_to_nearest_2min(time_str):
    """
    Round a time string (HH:MM) to the nearest 2-minute mark.
    """
    t = datetime.strptime(time_str, "%H:%M")
    minute = (t.minute // 2) * 2   # floor to nearest multiple of 2
    rounded = t.replace(minute=minute, second=0, microsecond=0)
    return rounded.strftime("%H:%M")

def calculate_mean_rvol(Rvol_data, end_time, start_time):

    # Filter by time window
    df_filtered = Rvol_data[
        (Rvol_data["Time"] >= start_time) & (Rvol_data["Time"] <= end_time)
    ].copy()

    if df_filtered.empty:
        print(f"No data available between {start_time} and {end_time}.")
        return pd.DataFrame()

    # Group by symbol and compute mean Rvol
    df_mean = (
        df_filtered.groupby("Symbol", as_index=False)["Rvol"]
        .mean()
        .round(2)
        .rename(columns={"Rvol": "Mean_Rvol"})
    )

    # Add start and end times as columns
    df_mean["Start_Time"] = start_time
    df_mean["End_Time"] = end_time

    return df_mean

def cumulative_volume_list(df_list, end_time, start_time):

    
    results = []
    
    for df in df_list:
        symbol = df['Symbol'].iloc[0]
        df_filtered = df[(df['Time'] >= start_time) & (df['Time'] <= end_time)]
        cum_vol = df_filtered['Volume'].sum() if not df_filtered.empty else 0.0
        results.append({'Symbol': symbol, 'Cumulative_Volume': cum_vol})
    
    return pd.DataFrame(results)





# Main function that servers Flask
def request_market_scan(project_config):

    host = project_config["ib_connection"]["host"]
    port = project_config["ib_connection"]["port"]
    clientId = project_config["ib_connection"]["clientId"]

    print("Fetching scan data")
    ib = IB()
    ib.connect(host, port, clientId)
    ticker_dict, df_scan = get_hot_by_volume_data(ib)

    df_stocks = display_stock_with_marketdata(df_scan, ticker_dict)


    # 1️⃣ Fetch raw 5-day history
    day5_history_datas = fetch_history_data(df_stocks, ib, days=5)

    # 2️⃣ Calculate average volumes
    avg_volumes = calculate_avg_volume(day5_history_datas)



    # Fetch today's data

    df_today_volumes = fetch_history_data(df_stocks, ib, days=1)
    #print(df_today_volumes)

    Rvol_data = compare_and_save_rvolumes(df_today_volumes, avg_volumes)



        # Try to get end_time from last row of today's data
    try:
        end_time = round_to_nearest_2min(df_today_volumes[0].iloc[-1]["Time"])
        if end_time < "11:00":
            end_time = "11:00"
    except Exception as e:
        print(f"Could not determine end_time from df_today: {e}")


    # Calculate mean Rvol using the function
    mean_rvols = calculate_mean_rvol(Rvol_data, end_time=end_time, start_time="11:00")

    # Example usage:
    cum_vol_df = cumulative_volume_list(df_today_volumes,end_time=end_time, start_time="11:00")




    # Merge by Symbol
    df_merged = pd.merge(df_stocks, mean_rvols, on="Symbol", how="left")

    # Sort by Mean_Rvol descending
    df_sorted = df_merged.sort_values(by="Mean_Rvol", ascending=False).reset_index(drop=True)



    # # # # # 3️⃣ Merge total volumes into df_stocks
    df_frame = df_sorted.merge(cum_vol_df, on='Symbol', how='left')

    # Replace infinite values with NaN first
    df_frame.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Option 1: Fill NaN values with 0 (or another default value)
    df_frame.fillna(0, inplace=True)



    print(df_frame)
    ib.disconnect()

    return df_frame


