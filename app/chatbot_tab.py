import os
import streamlit as st
import pandas as pd
from app.user_data_manager import load_user_data
from utils.llm import call_groq_llm

def render_chatbot_tab(user_id, api_key=None):
    st.markdown("## 💬 AI Finance Assistant")

    if api_key is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            st.warning("🚨 No API key provided for Groq. Please set GROQ_API_KEY as an environment variable.")
            return

    # Load recent transactions
    df = load_user_data(user_id)
    if df.empty:
        st.warning("No transaction data found.")
        return

    # Build full context
    salary = st.session_state.get(f"{user_id}_monthly_salary", "unknown")
    savings_goal = st.session_state.get(f"{user_id}_monthly_savings_goal", "unknown")
    budgets = st.session_state.get(f"{user_id}_category_budgets", {})
    budget_lines = [f"- {k}: ${v}" for k, v in budgets.items()]
    budget_text = "\n".join(budget_lines) if budgets else "No budget set."
    recent_context = df.tail(30).to_csv(index=False)

    full_context = f"""
User Profile:
- Monthly Salary: ${salary}
- Savings Goal: ${savings_goal}
- Budgets:
{budget_text}

Recent Transactions (last 30 records):
{recent_context}
"""

    # Unique session keys
    history_key = f"chat_history_{user_id}"
    input_key = f"chat_input_{user_id}"

    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # Display chat history
    for role, msg in st.session_state[history_key]:
        if role == "user":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 Assistant:** {msg}")

    # Chat input and submission at bottom
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("Type your question here:", key=input_key, label_visibility="collapsed")
        with col2:
            send = st.form_submit_button("Send")

    if send and user_input:
        # Append user message
        st.session_state[history_key].append(("user", user_input))

        # Build chat history context
        chat_log = "\n".join(
            f"{'User' if role == 'user' else 'Assistant'}: {msg}"
            for role, msg in st.session_state[history_key]
        )

        full_prompt = f"""
You are a helpful and smart personal finance AI assistant.
Here is the user's financial profile and recent data:

{full_context}

Here is our conversation so far:
{chat_log}

Continue the conversation by answering the user's latest message.
"""

        with st.spinner("🤖 Thinking..."):
            reply = call_groq_llm(full_prompt)

        st.session_state[history_key].append(("bot", reply))
        st.rerun()
