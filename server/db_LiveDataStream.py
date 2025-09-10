


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


def get_livestream_data(cursor, symbol: str):
    """
    Retrieve all data from the table named after the symbol and return it as a list of dicts.
    
    :param cursor: Database cursor
    :param symbol: Table name (must be validated)
    :return: List of dictionaries containing all rows
    """
    try:
        # Validate symbol: allow only letters, numbers, underscores
        if not symbol.isalnum() and "_" not in symbol:
            raise ValueError("Invalid table name")

        # Build query string safely after validation
        select_query = f'''
            SELECT *
            FROM "{symbol}"
            ORDER BY "Date" ASC, "Time" ASC;
        '''

        cursor.execute(select_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        df = [
            {
                "Symbol": str(row[columns.index("Symbol")]),
                "Date": str(row[columns.index("Date")]),
                "Time": str(row[columns.index("Time")]),
                "Open": float(row[columns.index("Open")]),
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

        return df

    except Exception as e:
        print(f"Error fetching data from table {symbol}: {e}")
        return None

