from db_connection import connect_db
import pandas as pd


def get_those_alarms(cursor):
    """
    Retrieve all data from the 'alarms' table and return it as a list of dictionaries.
    
    :return: List of dictionaries containing all rows from the 'alarms' table
    """
    try:


        # Define the SQL query to retrieve all data from the 'alarms' table
        select_query = """
                        SELECT * 
                        FROM alarms
                        ORDER BY "Time" ASC;
                    """
        
        # Execute the query
        cursor.execute(select_query)
        
        # Fetch all rows from the table
        rows = cursor.fetchall()

        # Get column names from the cursor description
        columns = [desc[0] for desc in cursor.description]

        # Convert data to list of dictionaries
        alarms_list = [
            {
                "Symbol": str(row[columns.index("Symbol")]),
                "Time": str(row[columns.index("Time")]),
                "Alarm": str(row[columns.index("Alarm")]),
                "Date": str(row[columns.index("Date")])
            }
            for row in rows
        ]


        # Return the list of alarms
        return alarms_list

    except Exception as e:
        print(f"Error: {e}")
        return None


def get_livestream_data(cursor):
    """
    Retrieve all data from the 'livestreamdata' table and return it as a Pandas DataFrame.
    
    :return: DataFrame containing all rows from the 'livestreamdata' table
    """
    try:

        # Define the SQL query to retrieve all data from the 'livestreamdata' table
        select_query = """
                        SELECT * 
                        FROM livestreamdata
                        ORDER BY "Date" ASC, "Time" ASC;
                    """
        
        # Execute the query
        cursor.execute(select_query)
        
        # Fetch all rows from the table
        rows = cursor.fetchall()

        # Get column names from the cursor description
        columns = [desc[0] for desc in cursor.description]

        # Convert data to list of dictionaries
        df = [
            {
                "Ticker": str(row[columns.index("Ticker")]),  # Assuming 'Ticker' exists in the table
                "Date": str(row[columns.index("Date")]),      # Assuming 'Date' exists in the table
                "Time": str(row[columns.index("Time")]),  # Convert 'Time' to string to make it JSON serializable
                "Open": float(row[columns.index("Open")]),  # Convert to float
                "High": float(row[columns.index("High")]),
                "Low": float(row[columns.index("Low")]),
                "Close": float(row[columns.index("Close")]), 
                "Volume": float(row[columns.index("Volume")]),
                "VWAP": float(row[columns.index("VWAP")]),
                "EMA9": float(row[columns.index("EMA9")]),
                "Relatr": float(row[columns.index("Relatr")])
            }
            for row in rows
        ]

        # Return the DataFrame
        return df

    except Exception as e:
        print(f"Error: {e}")
        return None