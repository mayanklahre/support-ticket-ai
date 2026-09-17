from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
st.set_page_config(page_title="AI Support Ticket Analyst", page_icon="🎫", layout="wide")
st.title("AI Support Ticket Analyst")
st.caption("Natural-language interpretation uses the API's configured local LLM. Pandas computes all answers.")


@st.cache_data(ttl=10)
def fetch_health() -> dict:
    response = requests.get(f"{API_URL}/health", timeout=5)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=20)
def fetch_anomalies() -> dict:
    response = requests.get(f"{API_URL}/anomalies", timeout=10)
    response.raise_for_status()
    return response.json()


try:
    health = fetch_health()
except requests.RequestException:
    st.error(f"The API is unavailable at {API_URL}. Start the FastAPI service first.")
    st.stop()

try:
    anomalies = fetch_anomalies()
except requests.RequestException:
    anomalies = {"summary": {"total": "n/a"}, "anomalies": []}

counts = health["status_counts"]
cols = st.columns(5)
for col, label, value in zip(cols, ["Total Tickets", "Open Tickets", "Escalated Tickets", "Resolved Tickets", "Anomalies"], [health["record_count"], counts.get("Open", 0), counts.get("Escalated", 0), counts.get("Resolved", 0), anomalies["summary"]["total"]]):
    col.metric(label, value)
st.caption(f"Dataset reference timestamp: {health['dataset_reference_date']} | Local LLM: {health['llm_status']}")

question = st.text_input("Ask a question about the support tickets", placeholder="How many tickets are currently open?")
if st.button("Ask", type="primary"):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        try:
            # Local models can need more than 30 seconds, especially on their first request.
            # Keep this slightly above the API's configured 120-second LLM timeout.
            response = requests.post(f"{API_URL}/query", json={"question": question}, timeout=135)
            if response.status_code == 503:
                st.error("The local LLM is unavailable. Start Ollama and pull the configured model.")
            elif not response.ok:
                st.error(response.json().get("detail", "The request could not be processed."))
            else:
                answer = response.json()
                st.subheader("Answer")
                st.write(answer["explanation"])
                result = answer["result"]
                if result["result_type"] == "scalar":
                    st.metric("Result", result["value"])
                else:
                    st.dataframe(pd.DataFrame(result["rows"]), width="stretch")
                with st.expander("Parsed interpretation"):
                    st.json(answer["parsed_query"])
        except requests.RequestException:
            st.error("The API request failed. Check that the backend is running.")

st.subheader("Anomaly dashboard")
st.write(anomalies["summary"])
if anomalies["anomalies"]:
    st.dataframe(pd.DataFrame(anomalies["anomalies"]), width="stretch")
else:
    st.info("No anomalies found.")
