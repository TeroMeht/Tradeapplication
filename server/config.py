from configparser import ConfigParser
import json

# Database config

def read_db_config(filename="database.ini", section="postgresql"):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
    db_config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_config[param[0]] = param[1]
    else:
        raise Exception(
            'Section {0} is not found in the {1} file.'.format(section, filename))
    return db_config

# Project config

# Function to read the JSON configuration
def read_project_config(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config