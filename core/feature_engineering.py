import pandas as pd

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds time-based features, lags, and rolling stats for forecasting models.
    Assumes df has columns ['ds', 'y'].
    """
    df = df.copy()
    df["dayofweek"] = df["ds"].dt.dayofweek
    df["quarter"] = df["ds"].dt.quarter
    df["month"] = df["ds"].dt.month
    df["dayofmonth"] = df["ds"].dt.day
    df["weekofyear"] = df["ds"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)

    for lag in [1, 2, 3, 7, 14, 30]:
        df[f"lag_{lag}"] = df["y"].shift(lag)
    df["rolling_7_mean"] = df["y"].rolling(7).mean()
    df["rolling_14_mean"] = df["y"].rolling(14).mean()
    df["rolling_30_mean"] = df["y"].rolling(30).mean()
    df["diff_1"] = df["y"].diff(1)
    df["diff_7"] = df["y"].diff(7)

    return df.dropna()
