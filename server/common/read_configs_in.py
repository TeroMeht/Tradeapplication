from configparser import ConfigParser
import json

import logging

logger = logging.getLogger(__name__)


def read_database_config(filename, section):
    """Parse the database.ini file and return connection parameters."""
    logger.info("Reading database config: %s [%s]", filename, section)
    parser = ConfigParser()
    parser.read(filename)
    if parser.has_section(section):
        return dict(parser.items(section))
    else:
        logger.error("Section %s not found in %s", section, filename)
        raise Exception(f"Section {section} not found in {filename}")

def read_project_config(filename):
    """Read a JSON project configuration file and return as dict."""
    logger.info("Reading project config: %s", filename)
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read project config %s: %s", filename, e)
        raise