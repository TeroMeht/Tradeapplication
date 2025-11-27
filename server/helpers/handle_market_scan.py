# scanner_utils.py

import pandas as pd

def handle_scandata_from_ib(df_scan: pd.DataFrame):
    """
    From IB Scanner DataFrame, extract only:
        - rank
        - symbol (from contractDetails.contract.symbol)
    Ensures everything is JSON serializable.
    """
    results = []

    for _, row in df_scan.iterrows():
        # Safely get contract details
        details = row.get("contractDetails", None)
        contract = None
        if isinstance(details, dict):
            contract = details.get("contract", None)
        elif details:
            # If it's an object with attribute 'contract'
            contract = getattr(details, "contract", None)

        # Extract symbol safely
        symbol = ""
        if isinstance(contract, dict):
            symbol = contract.get("symbol", "")
        elif contract and hasattr(contract, "symbol"):
            symbol = getattr(contract, "symbol", "")

        # Extract rank safely
        rank = row.get("rank", None)
        # Only convert numeric ranks
        if rank is not None:
            try:
                rank = int(rank)
            except:
                rank = None

        results.append({
            "symbol": str(symbol) if symbol else "",
            "rank": rank
        })

    return results