import streamlit as st
import requests
import json
from streamlit_webrtc import webrtc_streamer # For WS simulation; actually use API polling/WS

st.title("Real-Time Monitoring Dashboard")

# Tabs
tab1, tab2, tab3 = st.tabs(["Active Runs", "Alerts", "Logs"])

with tab1:
    # Fetch active runs (poll API or WS)
    if st.button("Refresh Runs"):
        # Simulate fetch
        runs = [
            {
                "id": "run1",
                "status": "running",
                "steps": 2
            },
            {
                "id": "run2",
                "status": "failed",
                "steps": 1
            }
        ]

        for run in runs:
            st.metric(f"Run {run['id']}", run["status"])
            if run["status"] == "failed":
                st.error("Failed step detected!")

with tab2:
    # Live alert feed
    alerts = st.session_state.get("alerts", [])
    for alert in alerts:
        st.warning(f"Low Inventory: {alert['low_skus']}")

with tab3:
    # Logs (tail-like)
    logs = [
        "2025-10-25 10:00: Workflow run1 reconciled orders",
        "2025-10-25 10:01: Low inventory alert for SKU1"
    ]
    for log in logs:
        st.text(log)

# WS Connection Simulation (connect to /ws/dashboard)
st.write("Connected to real-time updates via WebSocket.")
# In prod, use streamlit-ws or custom component for live feed