


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


