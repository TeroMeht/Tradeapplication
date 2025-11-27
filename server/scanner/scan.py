
from ib_async import IB, ScannerSubscription
from ib_async.contract import Contract, Stock,util
import pandas as pd
import numpy as np
from datetime import datetime



from scanner.scanner_presets import SCANNER_PRESETS
from typing import Tuple,Dict,List, Optional


def get_presets(name: str) -> dict:

    if name not in SCANNER_PRESETS:
        raise ValueError(
            f"Preset '{name}' not found. Available presets: {list(SCANNER_PRESETS.keys())}"
        )

    return SCANNER_PRESETS[name]


def run_scanner(ib: IB, preset_name: str, **overrides) -> Tuple[ScannerSubscription, pd.DataFrame]:

    # Load preset parameters and apply overrides
    params = get_presets(preset_name).copy()
    params.update(overrides)

    # Define scanner subscription
    sub = ScannerSubscription(**params)

    # Request scanner data
    df_scan = ib.reqScannerData(sub)
    df_scan = util.df(df_scan)

    return sub, df_scan

