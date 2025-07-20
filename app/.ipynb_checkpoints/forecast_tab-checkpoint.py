import streamlit as st
import pandas as pd
import plotly.express as px
import os
import joblib
from datetime import timedelta
from core.feature_engineering import create_features
from core.model_loader import forecast_with_personalization



def render_forecast_tab(df, user_id, categories):
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M")
    df["day"] = df["date"].dt.day_name()

    st.markdown("## Forecast Spending")

    f_col1, f_col2 = st.columns([2, 1])
    selected_cat = f_col1.selectbox("Select Category", categories)
    default_days = st.session_state.get(f"{user_id}_default_forecast_days", 30)
    n_days = f_col2.slider("Days Ahead", 1, 90, default_days)


    if st.button("Run Forecast"):
        # Step 1: Prepare input data
        cat_df = df[df["category"] == selected_cat].copy()
        cat_df = cat_df.groupby("date", as_index=False)["amount"].sum()
        cat_df = cat_df.rename(columns={"date": "ds", "amount": "y"})
        cat_df = cat_df.sort_values("ds")
        cat_df["ds"] = pd.to_datetime(cat_df["ds"])

        full_df = cat_df.copy()
        future_dates = [full_df["ds"].max() + timedelta(days=i) for i in range(1, n_days + 1)]

        forecasts = []
        safe_cat = selected_cat.lower().replace("/", "_")
        model_path = f"models/{safe_cat}_xgb.pkl"

        if not os.path.exists(model_path):
            st.warning("No global model found for this category.")
        else:
            model = joblib.load(model_path)

            
            for date in future_dates:
                last_df = pd.concat([full_df, pd.DataFrame({"ds": [date]})], ignore_index=True)
                last_df = last_df.sort_values("ds").reset_index(drop=True)
                last_df = last_df.ffill()
                temp = create_features(last_df)[-1:]
                X = temp.drop(columns=["ds", "y"], errors="ignore")

                if X.empty:
                    st.warning(f"⚠️ Skipping prediction for {date.date()} due to insufficient data.")
                    continue

                pred = model.predict(X)[0]
                forecasts.append((date, pred))
                full_df = pd.concat([full_df, pd.DataFrame({"ds": [date], "y": [pred]})], ignore_index=True)


            forecast_df = pd.DataFrame(forecasts, columns=["Date", "Forecasted Spend"])
            st.subheader(f"Forecast for {selected_cat} over {n_days} days")
            st.success(f"Estimated Total: ${forecast_df['Forecasted Spend'].sum():.2f}")
            fig3 = px.line(forecast_df, x="Date", y="Forecasted Spend", markers=True, title="Projected Daily Spending")
            st.plotly_chart(fig3, use_container_width=True)

            # === INSIGHT BOX ===
            if selected_cat in st.session_state[f"{user_id}_category_budgets"]:
                forecast_total = forecast_df["Forecasted Spend"].sum()
                budget_limit = st.session_state[f"{user_id}_category_budgets"].get(selected_cat, 0)

                diff = forecast_total - budget_limit
                status_color = "#f9c74f"  # neutral

                if diff > 0:
                    status_msg = f"⚠️ Your forecasted spending (${forecast_total:.2f}) exceeds your budget (${budget_limit:.2f}) by ${diff:.2f}."
                    status_color = "#f94144"  # red
                elif diff < -0.15 * budget_limit:
                    status_msg = f"✅ You're on track to stay under budget by ${-diff:.2f}."
                    status_color = "#43aa8b"  # green
                else:
                    status_msg = f"🟨 Your forecast is roughly equal to your budget (${forecast_total:.2f} vs ${budget_limit:.2f})."

                with st.container():
                    st.markdown(
                        f"""
                        <div style='background-color:{status_color};padding:15px 20px;border-radius:10px;color:white;margin-top:15px;font-size:16px;'>
                            <strong>Forecast Insight:</strong><br>{status_msg}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # === DOWNLOAD FORECAST CSV ===
            st.markdown("### Download Forecast Data")
            csv_data = forecast_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Forecast CSV",
                data=csv_data,
                file_name=f"{selected_cat.lower()}_forecast.csv",
                mime="text/csv",
                use_container_width=True
            )

    # === FORECAST VS BUDGET COMPARISON ===
    st.markdown("### Forecast vs Budget Across Categories")
    bar_data = []
    for cat in categories:
        forecast, _ = forecast_with_personalization(user_id=user_id, category=cat, df=df, n_days_ahead=30)
        budget = st.session_state[f"{user_id}_category_budgets"].get(cat, 0)
        bar_data.append({"category": cat, "type": "Forecast", "value": forecast})
        bar_data.append({"category": cat, "type": "Budget", "value": budget})

    bar_df = pd.DataFrame(bar_data)
    fig_bar = px.bar(
        bar_df, x="category", y="value", color="type", barmode="group",
        title="30-Day Forecast vs Budget by Category"
    )
    st.plotly_chart(fig_bar, use_container_width=True)