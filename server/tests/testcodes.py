



from common.read_configs_in import *
from database.db_functions import *



def main():

    # Load configs
    database_config = read_database_config(filename="database.ini", section="livestream")


    # Fetch last row from each table
    last_rows = fetch_last_row_from_each_table(database_config)
    if last_rows:
        print("\n📝 Last row from each table:")
        for table, row in last_rows.items():
            print(f"- {table}: {row}")
    else:
        print("⚠️ Failed to fetch last rows from tables.")


if __name__ == "__main__":
    main()