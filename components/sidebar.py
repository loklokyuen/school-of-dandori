import streamlit as st
from pipeline.ingest import sync_all
import pandas as pd
import time

def render_sidebar():
    with st.sidebar:
        if st.button("🔄 Sync with Firestore"):
            with st.spinner("Syncing latest courses..."):
                sync_all()
                st.session_state.pop("courses_df", None)
                st.session_state.df = pd.read_csv("./data/courses.csv")
            msg = st.success("Database synced")
            time.sleep(5)
            msg.empty()