import os
import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from core.feature_engineering import create_features

def train_global_models(data_path: str, output_dir: str = "models"):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(data_path, parse_dates=["date"])

    results = []

    for category in df["category"].unique():
        print(f"🔧 Training global model for: {category}")
        cat_df = df[df["category"] == category].copy()
        cat_df = cat_df.groupby(["user_id", "date"], as_index=False)["amount"].sum()
        cat_df = cat_df.rename(columns={"date": "ds", "amount": "y"})
        cat_df["ds"] = pd.to_datetime(cat_df["ds"])

        cat_df = create_features(cat_df)
        if cat_df.empty:
            print(f"⚠️ Skipping {category}: no usable data")
            continue

        X = cat_df.drop(columns=["ds", "y"]).select_dtypes(include="number")
        y = cat_df["y"]
        split_date = cat_df["ds"].max() - pd.Timedelta(days=30)
        train_data = cat_df[cat_df["ds"] <= split_date]
        test_data = cat_df[cat_df["ds"] > split_date]
        
        X_train = train_data.drop(columns=["ds", "y"]).select_dtypes(include="number")
        y_train = train_data["y"]
        X_test = test_data.drop(columns=["ds", "y"]).select_dtypes(include="number")
        y_test = test_data["y"]


        model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        print(f"✅ MAE for {category}: {mae:.2f}")


        safe_cat = category.lower().replace("/", "_")
        joblib.dump(model, os.path.join(output_dir, f"{safe_cat}_xgb.pkl"))
        print(f"✅ Saved {safe_cat}_xgb.pkl | MAE: {mae:.2f}")
        results.append((category, mae))

    return results
