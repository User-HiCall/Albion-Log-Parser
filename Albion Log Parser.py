import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Albion Log Parser", layout="wide")
st.title("Albion Log Parser")

raw_text = st.text_area(
    "Paste your Albion Online log here...",
    height=200,
    placeholder='"TimeStamp" "Player" "Action" "Amount"'
)

if st.button("parse it"):
    if not raw_text.strip():
        st.warning("Please paste your log data before parsing")
    else:
        try:
            df = pd.read_csv(
                io.StringIO(raw_text),
                sep='\t',
                engine='python',
                header=None,
                names=["timestamp", "player", "action", "amount"],
                quotechar='"'
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            if df[['timestamp', 'player', 'action', 'amount']].isna().any().any():
                raise ValueError("Each row must contain a valid timestamp, player, action, and amount")

            duplicate_mask = df.duplicated(
                subset=["timestamp", "player", "action", "amount"],
                keep="first"
            )
            duplicate_count = int(duplicate_mask.sum())
            if duplicate_count:
                st.warning(
                    f"{duplicate_count} duplicate transaction(s) found and excluded from the totals."
                )
                df = df.loc[~duplicate_mask].copy()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Actions", len(df))
            col2.metric("Total Amount", f"{df['amount'].sum():,}")
            col3.metric("Total Deposits", f"{df[df['action']=='Deposit']['amount'].sum():,}")
            col4.metric("Total Withdrawals", f"{df[df['action']=='Withdrawal']['amount'].sum():,}")
            
            st.markdown("----")
            
            summary = df.groupby('player').agg(
                total_deposit=('amount', lambda x: x[df.loc[x.index, 'action'] == 'Deposit'].sum()),
                total_withdrawal=('amount', lambda x: x[df.loc[x.index, 'action'] == 'Withdrawal'].sum()),
                net_balance=('amount', 'sum'),
                total_transactions=('amount', 'count')
            ).reset_index()
            
            st.subheader("Player Summary")
            st.dataframe(summary, use_container_width=True)
            
            st.subheader("Log History")
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error parsing log data: {e}")
