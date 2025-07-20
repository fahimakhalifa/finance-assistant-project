import streamlit as st
import pandas as pd


def render_budget_tab(df, user_id, categories, month_df):
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M")
    df["day"] = df["date"].dt.day_name()

    st.markdown("## Manage Category Budget")
    if "{user_id}_category_budgets" not in st.session_state:
        st.session_state[f"{user_id}_category_budgets"] = {cat: 100.0 for cat in categories}

    selected_budget_cat = st.selectbox("Select a category to manage budget", categories, key="budget_select")
    budget_val = st.session_state[f"{user_id}_category_budgets"].get(selected_budget_cat, 100.0)
    spent_val = month_df[month_df["category"] == selected_budget_cat]["amount"].sum()
    percent = int(min((spent_val / budget_val) * 100, 100)) if budget_val > 0 else 0

    st.markdown(f"**{selected_budget_cat}** — Spent: ${spent_val:.2f} / Budget: ${budget_val:.2f}")
    st.progress(percent)

    new_budget = st.number_input("Update Budget", min_value=0.0, value=float(budget_val), step=10.0)
    if st.button("Save Budget"):
        st.session_state[f"{user_id}_category_budgets"][selected_budget_cat] = new_budget
        st.success("Budget updated successfully.")

    st.markdown("## Monthly Budget Warnings")
    warnings = []
    for cat in categories:
        spent = month_df[month_df["category"] == cat]["amount"].sum()
        budget = st.session_state[f"{user_id}_category_budgets"].get(cat, 100.0)
        if spent > budget:
            warnings.append(("warning", f"You are over budget in {cat} by ${spent - budget:.2f} (Spent: ${spent:.2f} / Budget: ${budget:.2f})"))
        elif spent > 0.85 * budget:
            warnings.append(("info", f"You're nearing your budget in {cat}. Spent: ${spent:.2f} / Budget: ${budget:.2f}"))
    if warnings:
        for level, msg in warnings:
            if level == "warning":
                st.warning(msg)
            else:
                st.info(msg)
    else:
        st.success("All your categories are within budget this month.")
    # === MONTHLY SAVINGS GOAL TRACKER ===
    st.markdown("## Monthly Savings Goal")
    
    # Initialize savings goal if not set
    if "{user_id}_monthly_savings_goal" not in st.session_state:
        st.session_state[f"{user_id}_monthly_savings_goal"] = 1000  # default
    
    # Show input box to update the goal
    goal_input = st.number_input("Set your savings goal this month", min_value=0, value=st.session_state[f"{user_id}_monthly_savings_goal"], step=100)
    st.session_state[f"{user_id}_monthly_savings_goal"] = goal_input
    
    # Compute progress
    current_saved =st.session_state[f"{user_id}_monthly_salary"] - month_df["amount"].sum()
    progress = min(int((current_saved / goal_input) * 100), 100) if goal_input > 0 else 0
    
    # Show results
    st.markdown(f"**Saved So Far:** ${current_saved:.2f} of ${goal_input:.2f}")
    st.progress(progress)
    
    # Optional success/warning
    if current_saved >= goal_input:
        st.success("🎉 You've reached your savings goal!")
    elif current_saved > 0:
        st.info("You're making progress — keep it up!")
    else:
        st.warning("You haven't saved anything yet.")