import os
import joblib
import pandas as pd
from core.feature_engineering import create_features

def forecast_with_personalization(user_id: str, category: str, df: pd.DataFrame, n_days_ahead: int = 30,
                                   global_model_dir: str = "models",
                                   user_model_dir_root: str = "user_models") -> tuple:
    """
    Predicts spending using global + optional personalized model.
    Returns: (forecast_amount, model_used_note)
    """
    safe_cat = category.lower().replace("/", "_")

    cat_df = df[df["category"].str.lower() == category.lower()]
    if cat_df.empty:
        return None, "❌ No data for this category"

    cat_df = cat_df.groupby("date", as_index=False)["amount"].sum()
    cat_df = cat_df.rename(columns={"date": "ds", "amount": "y"})
    cat_df["ds"] = pd.to_datetime(cat_df["ds"])

    global_model_path = os.path.join(global_model_dir, f"{safe_cat}_xgb.pkl")
    if not os.path.exists(global_model_path):
        avg = cat_df["y"].tail(7).mean()
        return avg, "📉 Using last-week average (no model)"


    cat_df = create_features(cat_df)
    if cat_df.empty:
        return None, "⚠️ Not enough data after feature creation"

    X_latest = cat_df.drop(columns=["ds", "y"]).iloc[[-1]]
    global_model = joblib.load(global_model_path)
    base_forecast = global_model.predict(X_latest)[0]

    # Personalized residual
    residual_path = os.path.join(user_model_dir_root, user_id, f"{safe_cat}_residual.pkl")
    if os.path.exists(residual_path):
        residual_model = joblib.load(residual_path)
        residual_pred = residual_model.predict(X_latest)[0]
        total = round((base_forecast + residual_pred) * n_days_ahead, 2)
        return total, "🔁 Global + Personalized"
    else:
        total = round(base_forecast * n_days_ahead, 2)
        return total, "🌍 Global only"
