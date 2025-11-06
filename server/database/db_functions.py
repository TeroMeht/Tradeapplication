import psycopg2
import logging

logger = logging.getLogger(__name__)


def get_connection_and_cursor(database_config):
    """Create and return a database connection and cursor."""
    conn = psycopg2.connect(**database_config)
    if not conn:
        logger.error("Failed to connect to database.")
        raise Exception("Failed to connect to database.")
    cur = conn.cursor()
    return conn, cur




def fetch_alarms(database_config):
    """
    Retrieve all data from the 'alarms' table and return it as a list of dictionaries.
    """
    conn = None
    cur = None
    try:
        # Use the helper function to get a connection and cursor
        conn, cur = get_connection_and_cursor(database_config)

        # Define SQL query
        select_query = """
            SELECT "Symbol", "Time", "Alarm", "Date"
            FROM alarms
            ORDER BY "Time" ASC;
        """

        cur.execute(select_query)
        rows = cur.fetchall()

        # Get column names dynamically
        columns = [desc[0] for desc in cur.description]

        # Convert rows to list of dictionaries
        alarms_list = [dict(zip(columns, row)) for row in rows]

        return alarms_list

    except Exception as e:
        logger.error(f"Error fetching alarms: {e}")
        return None

    finally:
        # Always close database resources safely
        if cur:
            cur.close()
        if conn:
            conn.close()