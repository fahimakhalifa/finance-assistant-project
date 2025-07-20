
import os
import pandas as pd
import json
from core.train.train_residual import train_residuals_for_user

USER_DATA_DIR = "data/user_dumps"
SETTINGS_DIR = "data/user_settings"
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(SETTINGS_DIR, exist_ok=True)

def get_user_csv_path(user_id: str) -> str:
    return os.path.join(USER_DATA_DIR, f"{user_id}.csv")

def load_user_data(user_id: str) -> pd.DataFrame:
    path = get_user_csv_path(user_id)
    if not os.path.exists(path):
        return pd.DataFrame(columns=["date", "category", "amount"])
    return pd.read_csv(path, parse_dates=["date"])

def save_user_data(user_id: str, df: pd.DataFrame):
    df.to_csv(get_user_csv_path(user_id), index=False)

def retrain_user_model(user_id: str):
    user_path = get_user_csv_path(user_id)
    if os.path.exists(user_path):
        train_residuals_for_user(user_id=user_id, user_csv_path=user_path)

def get_user_settings_path(user_id: str) -> str:
    return os.path.join(SETTINGS_DIR, f"{user_id}_settings.json")

def load_user_settings(user_id: str) -> dict:
    path = get_user_settings_path(user_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_user_settings(user_id: str, settings: dict):
    path = get_user_settings_path(user_id)
    with open(path, "w") as f:
        json.dump(settings, f)
