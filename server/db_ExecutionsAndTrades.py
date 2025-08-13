from datetime import datetime, date, time


def get_execution_data(cursor):
    """
    Fetch all executions from the database and return the data,
    converting datetime, date, and time objects to strings for JSON serialization.
    """
    try:
        select_query = """
            SELECT * 
            FROM "executions"
            ORDER BY "Date" ASC;
        """
        cursor.execute(select_query)
        rows = cursor.fetchall()

        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description]
        
        # Convert rows to a list of dictionaries with column names as keys
        raw_data = []
        for row in rows:
            row_dict = {}
            for col_name, value in zip(columns, row):
                if isinstance(value, (datetime, date, time)):
                    row_dict[col_name] = value.isoformat()
                else:
                    row_dict[col_name] = value
            raw_data.append(row_dict)

        return raw_data

    except Exception as e:
        print(f"Error fetching execution data: {e}")
        return None
    


def get_trade_data(cursor):
    """
    Fetch all trades from the database and return the data,
    converting datetime, date, and time objects to strings for JSON serialization.
    """
    try:
        select_query = """
            SELECT * 
            FROM "trades"
            ORDER BY "Date" ASC;
        """
        cursor.execute(select_query)
        rows = cursor.fetchall()

        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description]
        
        # Convert rows to a list of dictionaries with column names as keys
        raw_data = []
        for row in rows:
            row_dict = {}
            for col_name, value in zip(columns, row):
                if isinstance(value, (datetime, date, time)):
                    row_dict[col_name] = value.isoformat()
                else:
                    row_dict[col_name] = value
            raw_data.append(row_dict)

        return raw_data

    except Exception as e:
        print(f"Error fetching trade data: {e}")
        return None    