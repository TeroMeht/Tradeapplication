import logging
import os

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

IB_SCANNER_LOG_FILE = os.path.join(LOG_DIR, "ib_scanner.log")

# Create a custom logger
ib_scanner_logger = logging.getLogger("ib_scanner")
ib_scanner_logger.setLevel(logging.INFO)

# Prevent double logging if handlers already added
if not ib_scanner_logger.handlers:
    file_handler = logging.FileHandler(IB_SCANNER_LOG_FILE)
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(formatter)

    ib_scanner_logger.addHandler(file_handler)
    ib_scanner_logger.propagate = False  # Keep logs out of global log file
