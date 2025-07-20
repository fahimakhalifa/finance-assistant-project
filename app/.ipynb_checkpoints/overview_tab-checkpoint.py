import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

def render_overview_tab(df, user_id):
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
         df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M")
    df["day"] = df["date"].dt.day_name()

    st.markdown("## User Settings")
    with st.expander("Adjust your preferences", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.setdefault(f"{user_id}_monthly_salary", 5000)
            salary_input = st.number_input("Monthly Salary", min_value=0, value=int(st.session_state[f"{user_id}_monthly_salary"]), step=100)
            st.session_state[f"{user_id}_monthly_salary"] = salary_input
        with col2:
            default_days = st.slider(
            "Default Forecast Days",
            min_value=7,
            max_value=90,
            value=st.session_state[f"{user_id}_default_forecast_days"]
        )
            st.session_state[f"{user_id}_default_forecast_days"] = default_days

          
    # === METRICS ROW ===
    st.markdown("## Monthly Overview")
    latest_month = df["month"].max()
    month_df = df[df["month"] == latest_month]
    spent = month_df["amount"].sum()
    salary = st.session_state[f"{user_id}_monthly_salary"]
    saved = salary - spent

    col1, col2, col3 = st.columns(3)
    col1.metric("Salary", f"${salary:.2f}")
    col2.metric("Spent", f"${spent:.2f}")
    col3.metric("Saved", f"${saved:.2f}")

    st.markdown("---")

    # === SPENDING TRENDS ===
    st.markdown("### Monthly Spending Trend")
    monthly = df.groupby("month")["amount"].sum().reset_index()
    monthly["month"] = monthly["month"].astype(str)
    fig = px.line(monthly, x="month", y="amount", markers=True, title="Total Monthly Spending")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Category Breakdown (This Month)")
    category_df = month_df.groupby("category")["amount"].sum().reset_index().sort_values("amount")
    fig2 = px.bar(category_df, x="amount", y="category", orientation="h", color="amount",
                  color_continuous_scale="blues", title="Top Spending Categories")
    st.plotly_chart(fig2, use_container_width=True)
    
    # === SPENDING GROWTH BY CATEGORY ===
    
    st.markdown("### Category Growth Since Last Month")
    
    prev_month = latest_month - 1
    this_month_df = df[df["month"] == latest_month]
    prev_month_df = df[df["month"] == prev_month]
    
    # Aggregate by category
    current = this_month_df.groupby("category")["amount"].sum()
    previous = prev_month_df.groupby("category")["amount"].sum()
    
    # Align categories
    all_cats = sorted(set(current.index).union(set(previous.index)))
    growth_data = []
    
    for cat in all_cats:
        current_val = current.get(cat, 0)
        prev_val = previous.get(cat, 0)
        if prev_val == 0:
            change_pct = 100 if current_val > 0 else 0
        else:
            change_pct = ((current_val - prev_val) / prev_val) * 100
        growth_data.append({"category": cat, "growth_percent": change_pct})
    
    growth_df = pd.DataFrame(growth_data).sort_values("growth_percent", ascending=False)
    fig_growth = px.bar(growth_df, x="growth_percent", y="category", orientation="h", title="Category Spending Growth (%)",
                        color="growth_percent", color_continuous_scale="RdBu", height=400)
    st.plotly_chart(fig_growth, use_container_width=True)


    # === ADVANCED SPENDING INSIGHTS ===
    st.markdown("### Advanced Spending Insights")
    df["weekday"] = df["date"].dt.day_name()

    dow_avg = df.groupby("weekday")["amount"].mean().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ).reset_index()
    fig_dow = px.bar(dow_avg, x="weekday", y="amount", title="Average Spending by Day of Week", color="amount",
                     color_continuous_scale="teal")
    st.plotly_chart(fig_dow, use_container_width=True)

    highest_day = df.groupby("date")["amount"].sum().sort_values(ascending=False).head(1)
    highest_date = highest_day.index[0].strftime("%Y-%m-%d")
    highest_amount = highest_day.iloc[0]
    st.markdown(f"**📌 Highest Spending Day:** {highest_date} — ${highest_amount:.2f}")

    daily_totals = df.groupby("date")["amount"].sum()
    volatility = daily_totals.std()
    st.markdown(f"**📉 Spending Volatility (Std Dev):** ${volatility:.2f}")

    # === DAILY TRANSACTIONS VIEW ===
    st.markdown("## Daily Spending Details")
    unique_dates = sorted(df["date"].dt.date.unique())
    selected_date = st.date_input("Select a date to view spending", value=unique_dates[-1], min_value=min(unique_dates), max_value=max(unique_dates))
    selected_day_df = df[df["date"].dt.date == selected_date]
    if selected_day_df.empty:
        st.info("No transactions found on this date.")
    else:
        breakdown = selected_day_df.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
        total = selected_day_df["amount"].sum()
        st.markdown(f"**Total Spending on {selected_date}:** ${total:.2f}")
        st.dataframe(breakdown, use_container_width=True)


        # === SPENDING VELOCITY GAUGE ===
    from datetime import date
    
    st.markdown("### Are You Spending Too Fast?")
    
    # Days in current month
    today = date.today()
    days_in_month = pd.Period(today.strftime("%Y-%m")).days_in_month
    day_of_month = today.day
    month_progress_pct = (day_of_month / days_in_month) * 100
    
    # Total spent and expected spend based on pacing
    total_spent_so_far = month_df["amount"].sum()
    expected_spend_by_now = (st.session_state[f"{user_id}_monthly_salary"] * (month_progress_pct / 100))
    pacing_status = ""
    
    if total_spent_so_far > expected_spend_by_now:
        pacing_status = "⚠️ You are spending faster than your salary allows. Slow down!"
        bar_color = "red"
    elif total_spent_so_far > 0.9 * expected_spend_by_now:
        pacing_status = "⚠️ You’re close to overspending at your current pace."
        bar_color = "orange"
    else:
        pacing_status = "✅ Your spending pace is on track!"
        bar_color = "green"
    
    # Show summary
    st.markdown(f"**Month Progress:** {month_progress_pct:.0f}%")
    st.markdown(f"**You’ve spent:** ${total_spent_so_far:.2f}")
    st.markdown(f"**Ideal spend by now:** ${expected_spend_by_now:.2f}")
    st.markdown(f"**Status:** {pacing_status}")
    
    # Gauge-style bar
    pacing_ratio = total_spent_so_far / expected_spend_by_now if expected_spend_by_now > 0 else 0
    progress_pct = min(int(pacing_ratio * 100), 100)
    
    st.progress(progress_pct)
