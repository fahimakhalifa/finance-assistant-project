import streamlit as st
import pandas as pd
from datetime import date
from app.user_data_manager import save_user_data, retrain_user_model, load_user_data


def render_transactions_tab(user_id):
    st.markdown("## 📒 Transaction History")

    # Load or initialize
    data_key = f"{user_id}_data"
    if data_key not in st.session_state:
        df = load_user_data(user_id)
        st.session_state[data_key] = df

    df = st.session_state[data_key]

    # === FORM TO ADD NEW RECORD ===
    st.markdown("### ➕ Add New Record")

    with st.form("add_record_form"):
        col1, col2, col3 = st.columns(3)
        new_date = col1.date_input("Date", value=date.today())
        new_cat = col2.text_input("Category")
        new_amt = col3.number_input("Amount", min_value=0.0, step=1.0)

        if st.form_submit_button("Add"):
            if new_cat and new_amt:
                new_row = pd.DataFrame([{
                    "date": pd.to_datetime(new_date),
                    "category": new_cat,
                    "amount": float(new_amt)
                }])
                st.session_state[data_key] = pd.concat([df, new_row], ignore_index=True)
                st.success("✅ New record added. Don’t forget to save!")
            else:
                st.warning("Please fill in all fields.")

    st.markdown("### ✏️ Edit or Delete Transactions")

    edited_df = st.data_editor(
        st.session_state[data_key],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_table"
    )

    # === SAVE CHANGES ===
    if st.button("💾 Save Changes"):
        try:
            save_user_data(user_id, edited_df)
            retrain_user_model(user_id)
            st.session_state[data_key] = edited_df
            st.success("✅ Data saved and model retrained!")
        except Exception as e:
            st.error(f"Failed to save: {e}")
