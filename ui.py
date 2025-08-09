import streamlit as st
import requests

# --- Config ---
API_URL = "http://localhost:8000"  # Change if deployed

st.set_page_config(page_title="Sassy Python", layout="centered")

# --- Session State Init ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_stats" not in st.session_state:
    st.session_state.quiz_stats = {"score": 0, "correct": 0, "total": 0}

# --- UI Title ---
st.title("🐍 Sassy Python")
st.caption("Your sarcastic Python tutor")

# --- Mode Selector ---
mode = st.sidebar.selectbox("Choose Mode", ["ask", "code", "quiz"])

# --- Ask Mode ---
if mode == "ask":
    question = st.text_area("Ask Sassy Python a Python question:")
    if st.button("Ask"):
        if not question.strip():
            st.warning("Please type something first.")
        else:
            res = requests.post(f"{API_URL}/chat", json={"mode": "ask", "content": question})
            if res.ok:
                st.markdown(res.json()["reply"])
            else:
                st.error("Error: Could not get a reply.")

# --- Code Mode ---
elif mode == "code":
    code = st.text_area("Paste your Python code for a roast + explanation:")
    if st.button("Roast Me"):
        if not code.strip():
            st.warning("Please paste your code first.")
        else:
            res = requests.post(f"{API_URL}/chat", json={"mode": "code", "content": code})
            if res.ok:
                st.markdown(res.json()["reply"])
            else:
                st.error("Error: Could not get a roast.")

# --- Quiz Mode ---
elif mode == "quiz":
    if st.button("Get a New Question"):
        res = requests.post(f"{API_URL}/chat", json={"mode": "quiz"})
        if res.ok:
            st.session_state.quiz_data = res.json()["reply"]
        else:
            st.error("Error: Could not load quiz.")

    quiz = st.session_state.quiz_data
    if quiz:
        st.subheader(quiz["question"])
        if quiz.get("code"):
            st.code(quiz["code"], language="python")

        choice = st.radio("Choose an answer:", quiz["options"], index=None)

        if st.button("Submit Answer"):
            st.session_state.quiz_stats["total"] += 1
            correct_answer = quiz["options"][quiz["answer"]]
            if choice == correct_answer:
                st.success("Correct! 🎉")
                st.session_state.quiz_stats["correct"] += 1
                st.session_state.quiz_stats["score"] += quiz["score"]
            else:
                st.error(f"Wrong! Correct answer: {correct_answer}")
                roast_res = requests.post(f"{API_URL}/roast", json={
                    "question": quiz["question"],
                    "user_answer": choice,
                    "correct_answer": correct_answer
                })
                if roast_res.ok:
                    st.markdown(roast_res.json()["roast"])

        st.markdown(f"**Score:** {st.session_state.quiz_stats['score']} points")
        st.markdown(f"**Correct Answers:** {st.session_state.quiz_stats['correct']} / {st.session_state.quiz_stats['total']}")