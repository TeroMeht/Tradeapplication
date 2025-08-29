import pandas as pd


# Function to calculate VWAP
def calculate_vwap(historical_df):
    # Initialize VWAP column with float zeros
    historical_df['VWAP'] = 0.0  # Explicitly set to float

    # Calculate OHLC4 and add it as a new column
    historical_df['OHLC4'] = (historical_df['Open'] + historical_df['High'] + historical_df['Low'] + historical_df['Close']) / 4


    for i, row in historical_df.iterrows():
        # Use OHLC4 instead of Close for VWAP calculation
        cumulative_volume = historical_df.loc[:i, 'Volume'].sum()
        cumulative_price_volume = (historical_df.loc[:i, 'OHLC4'] * historical_df.loc[:i, 'Volume']).sum()
        historical_df.at[i, 'VWAP'] = cumulative_price_volume / cumulative_volume if cumulative_volume != 0 else 0.0
        historical_df['VWAP'] = historical_df['VWAP'].round(2)
        
    # Drop the OHLC4 column if it's not needed in the final output
    historical_df.drop(columns=['OHLC4'], inplace=True)

    return historical_df

#Edellyttää että VWAP historical_dfsetistä jo löytyy
def calculate_vwap_relative_atr(historical_df, atr_value):

    if atr_value is None or atr_value == 0:
        raise ValueError("Invalid ATR value. Cannot divide by zero.")

    # Calculate Relative ATR
    historical_df['Relatr'] = (historical_df['VWAP'] - historical_df['Close']) / atr_value
        # Round the Relatr column to 2 decimal places
    historical_df['Relatr'] = historical_df['Relatr'].round(2)

    return historical_df

def calculate_ema9(historical_df):

    if 'Close' not in historical_df.columns:
        raise ValueError("The historical_dfFrame must contain a 'Close' column.")

    # Calculate EMA9 using pandas' `ewm` method
    historical_df['EMA9'] = historical_df['Close'].ewm(span=9, adjust=False).mean().round(2)
    return historical_df

def calculate_14day_atr_df(historical_df, period=14):
    """
    Calculate 14-day ATR for all rows and return a DataFrame with ATR column.
    """
    df = historical_df.copy()
    df.columns = [col.capitalize() for col in df.columns]

    # Previous close
    df['Prev_Close'] = df['Close'].shift(1)

    # True Range (TR)
    df['TR'] = df.apply(
        lambda row: max(
            row['High'] - row['Low'],
            abs(row['High'] - row['Prev_Close']) if pd.notnull(row['Prev_Close']) else row['High'] - row['Low'],
            abs(row['Low'] - row['Prev_Close']) if pd.notnull(row['Prev_Close']) else row['High'] - row['Low']
        ),
        axis=1
    )

    # ATR: exponential moving average of TR
    df['ATR14'] = df['TR'].ewm(span=period, adjust=False).mean()

    # Drop intermediate columns
    df.drop(columns=['Prev_Close', 'TR'], inplace=True)

    return df



# Dynaamiset laskennat sisään tulevalle riville
def calculate_next_vwap(new_row, historical_df):

    try:
        # Ensure numeric types
        df = historical_df.copy()
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Compute OHLC4 for historical data
        if not df.empty:
            df["OHLC4"] = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
        else:
            df["OHLC4"] = pd.Series(dtype=float)

        # Compute OHLC4 for new row
        new_row_ohlc4 = (new_row[3] + new_row[4] + new_row[5] + new_row[6]) / 4

        # Cumulative VWAP calculation
        cumulative_volume = df["Volume"].sum() + float(new_row[7])
        cumulative_price_volume = (df["OHLC4"] * df["Volume"]).sum() + (new_row_ohlc4 * float(new_row[7]))

        vwap_value = round(cumulative_price_volume / cumulative_volume, 2) if cumulative_volume != 0 else 0.0

        # Append VWAP to new_row
        new_row.append(float(vwap_value))

        return new_row

    except Exception as e:
        print(f"Error calculating VWAP for {new_row[0]}: {e}")
        new_row.append(0.0)
        return new_row

    except Exception as e:
        print(f"Error in calculate_next_vwap_ema9 for {new_row[0]}: {e}")
        return new_row

def calculate_next_ema9(new_row, historical_df):
    """
    Calculate EMA9 for a new_row based on historical_df using pandas ewm.
    Appends the EMA9 value to new_row.
    """
    try:
        # Build a DataFrame including historical data + new row
        df = historical_df.copy()

        # Ensure 'Close' is numeric
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce").fillna(0)

        # Append new row Close
        new_close = float(new_row[6])  # Close is at index 6
        new_row_df = pd.DataFrame([{"Close": new_close}])
        df = pd.concat([df[["Close"]], new_row_df], ignore_index=True)

        # Calculate EMA9
        df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean().round(2)

        # Append the latest EMA9 to new_row
        new_row.append(float(df["EMA9"].iloc[-1]))

        return new_row

    except Exception as e:
        print(f"Error calculating EMA9 for {new_row[0]}: {e}")
        new_row.append(0.0)
        return new_row

def calculate_next_relatr(new_row, atr_dict):
    try:
        # Get symbol from the new_row
        symbol = new_row[0]  # Assuming symbol is the first element

        atr_value = atr_dict.get(symbol, None)
        if atr_value is None or atr_value == 0:
            print(f"ATR value missing or zero for {symbol}")
            return new_row  # Return the row even if Relatr can't be calculated

        VWAP = new_row[8]   # VWAP index
        Close = new_row[6]  # Close index

        relatr_value = round((VWAP - Close) / atr_value, 2)

        new_row.append(float(relatr_value))  # Ensure float
        return new_row

    except Exception as e:
        print(f"Error calculating Relatr for {symbol}: {e}")
        return new_row
    




# Laskee positio koon kun tiedetään nämä
def calculate_position_size(entry_price, stop_price, risk):

    try:
        risk_per_unit = entry_price - stop_price
        if risk_per_unit == 0:
            raise ValueError("Entry price and stop price cannot be the same.")
        
        position_size = int(risk / risk_per_unit)  # force integer
        return position_size
    
    except Exception as e:
        print("Error calculating position size:", e)
        return None