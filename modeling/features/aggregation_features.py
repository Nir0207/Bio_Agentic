from __future__ import annotations

import pandas as pd


def fill_missing_with_zero(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    numeric_columns = frame.select_dtypes(include=["number"]).columns
    frame[numeric_columns] = frame[numeric_columns].fillna(0.0)
    return frame
