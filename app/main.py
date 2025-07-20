# === CLEAR SESSION FULLY ON LOGOUT ===
def clear_user_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# === Core Python ===
import os
import sys
from datetime import timedelta, date
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# === Internal Modules ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from core.model_loader import forecast_with_personalization
from core.feature_engineering import create_features
from auth.user_auth import get_authenticator, CONFIG_PATH
from app.user_data_manager import (
    load_user_data, save_user_data, retrain_user_model,
    load_user_settings, save_user_settings
)
from app.overview_tab import render_overview_tab
from app.forecast_tab import render_forecast_tab
from app.budget_tab import render_budget_tab
from app.transactions_tab import render_transactions_tab
from app.chatbot_tab import render_chatbot_tab
from streamlit_authenticator.utilities.hasher import Hasher

# === CONFIG ===
os.environ["GROQ_API_KEY"] = "your_key_here"
st.set_page_config(page_title="Finance Assistant V2", layout="wide")

# === AUTHENTICATION FLOW ===
authenticator = get_authenticator()
authenticator.login("main", max_login_attempts=3)
auth_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")
name = st.session_state.get("name")

if auth_status is False:
    st.error("🚫 Incorrect username or password.")
    st.stop()

elif auth_status is None:
    st.warning("Please enter your username and password.")
    st.markdown("### 🆕 Or Register Below", unsafe_allow_html=True)
    with st.form("register_form"):
        new_username = st.text_input("Choose a username")
        new_name = st.text_input("Full name")
        new_password = st.text_input("Password", type="password")
        register_button = st.form_submit_button("Create Account")

        if register_button:
            if new_username and new_name and new_password:
                with open(CONFIG_PATH, 'r') as file:
                    config = yaml.load(file, Loader=SafeLoader)
                if new_username in config['credentials']['usernames']:
                    st.warning("🚫 Username already exists.")
                else:
                    hashed_pw = Hasher().hash(new_password)
                    config['credentials']['usernames'][new_username] = {
                        'name': new_name,
                        'password': hashed_pw
                    }
                    with open(CONFIG_PATH, 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    st.success("✅ Account created! Please login.")
                    st.rerun()
            else:
                st.warning("Please fill out all fields.")
    st.stop()

# === Ensure Fresh Page After Login
if auth_status and not st.session_state.get("has_refreshed"):
    st.session_state["has_refreshed"] = True
    st.rerun()

# === Authenticated Session Begins ===
st.sidebar.success(f"Welcome {name}")
user_id = username
user_csv_path = f"data/user_dumps/{user_id}.csv"

# === Onboarding Form (Generate CSV if it doesn't exist)
if not os.path.exists(user_csv_path):
    st.markdown("### 👋 Welcome! Let’s set up your assistant")

    income = st.number_input("💰 What’s your monthly salary?", min_value=0, value=3000, step=100)
    categories = st.multiselect("🗂️ Your main spending categories", ["Food", "Rent", "Transport", "Entertainment", "Shopping", "Utilities", "Other"])

    st.markdown("### 📊 Estimated Monthly Spending:")
    budget_inputs = {}
    for cat in categories:
        budget_inputs[cat] = st.number_input(f"{cat}", min_value=0, value=100, step=10)

    if st.button("🚀 Create My Profile") and categories:
        # Save CSV
        df = pd.DataFrame([
            {"date": date.today(), "category": cat, "amount": amt}
            for cat, amt in budget_inputs.items()
        ])
        df.to_csv(user_csv_path, index=False)

        # Save Settings
        save_user_settings(user_id, {
            "monthly_salary": income,
            "default_forecast_days": 30,
            "category_budgets": budget_inputs,
            "monthly_savings_goal": int(income * 0.2)
        })

        st.success("🎉 Profile created! Loading your dashboard...")
        st.rerun()
    else:
        st.stop()

# === Load Data + Settings
df = load_user_data(user_id)
if df.empty:
    st.info("📭 No data found. Please go to 'Transactions' tab to add.")
    st.stop()

settings = load_user_settings(user_id)
# Inject per-user settings into session_state if not already set
st.session_state.setdefault(f"{user_id}_monthly_salary", settings.get("monthly_salary", 5000))
st.session_state.setdefault(f"{user_id}_default_forecast_days", settings.get("default_forecast_days", 30))
st.session_state.setdefault(f"{user_id}_category_budgets", settings.get("category_budgets", {}))
st.session_state.setdefault(f"{user_id}_monthly_savings_goal", settings.get("monthly_savings_goal", 1000))

salary = settings.get("monthly_salary", 5000)
default_days = settings.get("default_forecast_days", 30)
budgets = settings.get("category_budgets", {})
savings_goal = settings.get("monthly_savings_goal", 1000)

# === Logout Behavior
if authenticator.logout("Logout", "sidebar"):
    save_user_settings(user_id, {
        "monthly_salary": salary,
        "default_forecast_days": default_days,
        "category_budgets": budgets,
        "monthly_savings_goal": savings_goal
    })
    clear_user_session()
    st.rerun()

# === Preprocess Data
if not pd.api.types.is_datetime64_any_dtype(df["date"]):
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["month"] = df["date"].dt.to_period("M")
df["day"] = df["date"].dt.day_name()
categories = sorted(df["category"].unique())
latest_month = df["month"].max()
month_df = df[df["month"] == latest_month]

# === Render Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🔮 Forecast", "💼 Budget", "📒 Transactions", "🤖 Assistant"])
with tab1:
    render_overview_tab(df, user_id)
with tab2:
    render_forecast_tab(df, user_id, categories)
with tab3:
    render_budget_tab(df, user_id, categories, month_df)
with tab4:
    render_transactions_tab(user_id)
with tab5:
    render_chatbot_tab(user_id)
