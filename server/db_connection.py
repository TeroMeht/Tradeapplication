import psycopg2
from configparser import ConfigParser
import json

# ✅ Database config function
def db_config(filename, section):

    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        for key, value in parser.items(section):
            db[key] = value
    else:
        raise Exception(f"Section {section} not found in the {filename} file.")
    return db

# ✅ Function to connect to the database
def connect_db(db_filename, section):

    try:
        params = db_config(db_filename, section)
        return psycopg2.connect(**params)
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        return None

# ✅ Project-level JSON config
def read_project_config(filename):

    with open(filename, 'r') as f:
        return json.load(f)
