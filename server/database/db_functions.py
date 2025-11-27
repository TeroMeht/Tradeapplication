import psycopg2
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def get_connection_and_cursor(database_config):
    """Create and return a database connection and cursor."""
    conn = psycopg2.connect(**database_config)
    if not conn:
        logger.error("Failed to connect to database.")
        raise Exception("Failed to connect to database.")
    cur = conn.cursor()
    return conn, cur

def fetch_last_n_rows(database_config, table_name, n):
    """
    Retrieve the last 'n' rows from the specified table and return it as a list of dictionaries.
    
    :param database_config: Database connection config.
    :param table_name: The name of the table to query.
    :param n: The number of rows to fetch (default is 10).
    :return: List of dictionaries with table rows or None in case of error.
    """
    conn = None
    cur = None
    try:
        # Use the helper function to get a connection and cursor
        conn, cur = get_connection_and_cursor(database_config)

        # SQL query to fetch the last n rows from the specified table
        select_query = f"""
            SELECT * FROM {table_name}
            ORDER BY "Time" DESC
            LIMIT {n};
        """
        cur.execute(select_query)
        rows = cur.fetchall()

        # Get column names dynamically
        columns = [desc[0] for desc in cur.description]

        # Convert rows to a list of dictionaries
        rows_list = [dict(zip(columns, row)) for row in rows]

        return rows_list

    except Exception as e:
        logger.error(f"Error fetching data from table {table_name}: {e}")
        return None

    finally:
        # Always close database resources safely
        if cur:
            cur.close()
        if conn:
            conn.close()



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


# skip livedata and alarms table
def fetch_all_table_names(database_config):
    """
    Retrieve all table names from the public schema of the PostgreSQL database.
    """
    conn = None
    cur = None
    try:
        conn, cur = get_connection_and_cursor(database_config)

        # SQL command to list all table names in the public schema
        select_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name NOT IN ('livedata', 'alarms')
                ORDER BY table_name;
        """

        cur.execute(select_query)
        rows = cur.fetchall()

        # Convert to simple list of table names
        table_names = [row[0] for row in rows]

        logger.debug(f"Fetched {len(table_names)} tables.")
        return table_names

    except Exception as e:
        logger.error(f"Error fetching table names: {e}")
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def fetch_last_row_from_each_table(database_config):
    """
    Fetch the last row from each table in the public schema
    (excluding 'livedata' and 'alarms').
    Returns a dictionary with table names as keys and last row as values.
    """
    last_rows = {}
    conn = None
    cur = None
    try:
        table_names = fetch_all_table_names(database_config)
        if not table_names:
            logger.warning("No tables found to fetch data from.")
            return last_rows

        conn, cur = get_connection_and_cursor(database_config)

        for table in table_names:
            try:
                # Query to get the last row based on primary key or insertion order
                query = f"""
                    SELECT *
                    FROM {table}
                    ORDER BY "Time" DESC
                    LIMIT 1;
                """
                cur.execute(query)
                row = cur.fetchone()
                if row:
                    col_names = [desc[0] for desc in cur.description]
                    row_dict = dict(zip(col_names, row))

                    # Convert values to JSON-serializable
                    for k, v in row_dict.items():
                        if hasattr(v, "isoformat"):  # datetime.date or datetime.time
                            row_dict[k] = v.isoformat()
                        elif isinstance(v, Decimal):
                            row_dict[k] = float(v)

                    last_rows[table] = row_dict
                else:
                    last_rows[table] = None

            except Exception as e:
                last_rows[table] = None

        return last_rows

    except Exception as e:
        logger.error(f"Error in fetching last rows from tables: {e}")
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()