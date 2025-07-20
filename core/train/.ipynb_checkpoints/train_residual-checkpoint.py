import os
import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from core.feature_engineering import create_features

def train_residuals_for_user(user_id: str, user_csv_path: str,
                              global_model_dir: str = "models",
                              output_dir_root: str = "user_models"):
    df = pd.read_csv(user_csv_path, parse_dates=["date"])
    user_dir = os.path.join(output_dir_root, user_id)
    os.makedirs(user_dir, exist_ok=True)

    for category in df["category"].unique():
        print(f"\n🎯 Training residual for: {category}")
        safe_cat = category.lower().replace("/", "_")
        global_model_path = os.path.join(global_model_dir, f"{safe_cat}_xgb.pkl")
        if not os.path.exists(global_model_path):
            print("❌ Global model missing, skipping")
            continue

        cat_df = df[df["category"] == category].copy()
        cat_df = cat_df.groupby("date", as_index=False)["amount"].sum()
        cat_df = cat_df.rename(columns={"date": "ds", "amount": "y"})
        cat_df["ds"] = pd.to_datetime(cat_df["ds"])

        cat_df = create_features(cat_df)
        if cat_df.empty:
            print("⚠️ Not enough data")
            continue

        X = cat_df.drop(columns=["ds", "y"])
        y = cat_df["y"]
        global_model = joblib.load(global_model_path)
        base_pred = global_model.predict(X)
        cat_df["residual"] = y - base_pred

        X = X.copy()
        y = cat_df["residual"]
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

        residual_model = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
        residual_model.fit(X_train, y_train)
        mae = mean_absolute_error(y_val, residual_model.predict(X_val))

        out_path = os.path.join(user_dir, f"{safe_cat}_residual.pkl")
        joblib.dump(residual_model, out_path)
        print(f"✅ Saved {out_path} | Residual MAE: {mae:.2f}")
