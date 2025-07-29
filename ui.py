import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"  # Your FastAPI endpoint

st.set_page_config(page_title="Sassy Python", page_icon="🐍", layout="centered")
st.title("🐍 Sassy Python – AI Tutor & Roaster")

# Mode selector
mode = st.selectbox("Choose Mode:", ["ask", "code", "quiz"])

# User input box
user_input = st.text_area("Your Question / Code:", height=150)

# Submit button
if st.button("Send"):
    if not user_input.strip():
        st.warning("Please type something first!")
    else:
        with st.spinner("Thinking..."):
            payload = {"mode": mode, "content": user_input}
            try:
                response = requests.post(API_URL, json=payload)
                data = response.json()

                if mode == "quiz":
                    st.success(f"**Question:** {data['reply']['question']}")
                    st.info(f"**Hint:** {data['reply']['hint']} (Score: {data['reply']['score']})")
                else:
                    st.success(f"**Response:** {data['reply']}")

            except Exception as e:
                st.error(f"Error: {e}")
