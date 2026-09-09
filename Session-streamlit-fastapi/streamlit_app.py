import os
import requests
import streamlit as st

API_URL = "http://localhost:8000/agent"

st.set_page_config(page_title ="Support Agent Chat")
st.title("Customer Support RAG Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask a support question...")

if prompt:
    st.session_state.messages.append({"role" : "user", "content" :prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        response = requests.post(API_URL, json={"question":prompt}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        answer = payload.get("answer", "No answer return by the agent")
    except requests.RequestException as ex:
        answer = f" The agent is not available right now. Error {ex}"

    st.session_state.messages.append({"role" : "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

with st.sidebar:
    st.subheader("Agent health")