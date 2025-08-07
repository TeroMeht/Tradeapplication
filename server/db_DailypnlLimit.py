
from datetime import datetime
def get_all_pnls(cursor):
    """
    Retrieve all PnL rows from the 'pnl' table, including all relevant columns.
    Converts the 'Time' to a more readable format if it's a datetime object.

    :param cursor: Database cursor
    :return: List of dictionaries representing all PnL rows or an empty list if no data found
    """
    try:
        query = """
            SELECT *
            FROM pnl
            ORDER BY "Time" DESC;  -- You can adjust this ordering as needed
        """
        cursor.execute(query)
        results = cursor.fetchall()  # Fetch all rows

        if results:
            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]

            # Map the results to dictionaries dynamically
            rows = []
            for result in results:
                row = dict(zip(columns, result))

                # If 'Time' is a datetime object, format it directly
                if isinstance(row["Time"], datetime):
                    row["Time"] = row["Time"].strftime("%Y-%m-%d %H:%M:%S")

                rows.append(row)

            return rows

        return []

    except Exception as e:
        print(f"Error fetching PnL data: {e}")
        return []