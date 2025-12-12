import math
from logs.ib_scanner_logger import ib_scanner_logger

def sanitize_for_json(obj):
    """
    Recursively sanitize data to ensure it is valid JSON.
    Converts:
    - NaN → None
    - Inf → None
    - -Inf → None
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]

    return obj  # int, str, bool, None are returned as-is


def log_scan_results(preset, results):
    ib_scanner_logger.info(f"=== Scan results for preset='{preset}' ({len(results)} items) ===")

    for item in results:
        symbol = item.get("symbol")
        rank = item.get("rank")
        last = item.get("last_price")
        yclose = item.get("yesterday_close")
        pct = item.get("change_pct")

        ib_scanner_logger.info(
            f"{symbol} | rank={rank} | last={last} | yclose={yclose} | change={pct}%"
        )

    ib_scanner_logger.info("=== End of scan ===\n")