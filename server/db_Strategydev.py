
from db_connection import connect_db
import pandas as pd


def get_30mindataIB():
    #Ticker ja sitten date johon asti haetaan, se date mukaan lukien. Otetaan vaikka viimeiset 10pv ja se voi olla parametrina
    pass
def get_dailydataIB():
    #Ticker ja sitten date johon asti haetaan, se date mukaan lukien. Tämä voi olla vaikka viimeiset 6kk dataa
    pass

def return_setup_by_id(cursor, id):

    try:
        # SQL query to fetch data filtered by id
        query = """
        SELECT * FROM setup WHERE id = %s;  -- Replace 'setup' with your actual table name
        """

        # Execute the query with id as a parameter
        cursor.execute(query, (id,))

        # Fetch all rows and column names
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Create a DataFrame from the query result
        df = pd.DataFrame(rows, columns=columns)
        # Check if there's a 'Date' column in the DataFrame
        if 'Date' in df.columns:
            # Convert 'Date' column to 'YYYY-MM-DD' format
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

        # Return the DataFrame
        return df

    except Exception as e:
        # Handle any exceptions that may occur
        print(f"Error occurred while fetching data for id {id}: {str(e)}")

        # Return an empty DataFrame in case of error
        return pd.DataFrame()  # Return an empty DataFrame to indicate an error

def get_setup_data(userId):
    try:
        # Database connection settings
        conn = connect_db()
        cursor = conn.cursor()
        df = return_setup_by_id(cursor,userId)

    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")
    finally:
        cursor.close()
        conn.close()
        print(f"Closing database connection")

    return df

def return_price_data_by_tickerdate(cursor, ticker, date, marketdata):
 
    # Determine the table name based on the timeframe
    table_name = f"{marketdata}"  # e.g., "minute_data", "hourly_data", "daily_data"
    
    # Construct SQL query using parameterized placeholders (%s)
    query = """
    SELECT * FROM {} 
    WHERE "Ticker" = %s 
    AND "Date" = %s
    ORDER BY "Time" ASC;
    """.format(table_name)

    print(ticker)
    # Execute the query
    cursor.execute(query, (ticker, date))
    
    # Fetch all rows and column names
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    # Convert data to list of dictionaries
    df = [
        {
            "Time": row[columns.index("Time")],  # Assuming 'Time' exists in the table
            "Open": float(row[columns.index("Open")]),  # Convert to float
            "High": float(row[columns.index("High")]),
            "Low": float(row[columns.index("Low")]),
            "Close": float(row[columns.index("Close")]),
            "Volume": float(row[columns.index("Volume")]),
            "VWAP": float(row[columns.index("VWAP")]),
            "EMA9": float(row[columns.index("EMA9")])
        }
        for row in rows
    ]
    # Return the fetched data
    return df

def get_price_data(ticker, date, timeframe):
    try:
        # Database connection settings
        conn = connect_db()
        cursor = conn.cursor()
        print(ticker, date, timeframe)
        # Call the function to fetch price data based on ticker, date, and timeframe
        df = return_price_data_by_tickerdate(cursor, ticker, date, timeframe)

    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")
    finally:
        cursor.close()
        conn.close()
        print(f"Closing database connection")

        return df