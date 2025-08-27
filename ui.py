import streamlit as st
import requests

# --- Config ---
API_URL = "http://localhost:8000"  # change when you deploy

st.set_page_config(page_title="Sassy Python", page_icon="🐍", layout="wide")

# --- Session State ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_stats" not in st.session_state:
    st.session_state.quiz_stats = {"score": 0, "correct": 0, "total": 0}

# --- Header ---
st.title("🐍 Sassy Python")
st.caption("Your sarcastic Python tutor. Use the tabs below: Ask • Code • Quiz")

# --- Tabs ---
tab_ask, tab_code, tab_quiz = st.tabs(["💬 Ask", "📝 Code", "🎯 Quiz"])

# ---------------------------
# 💬 Ask tab
# ---------------------------
with tab_ask:
    st.subheader("Ask a Python question")
    st.markdown("Type any Python question. I’ll answer—with a bit of attitude.")
    question = st.text_area("Your question:", key="ask_input")

    if st.button("Ask", key="ask_btn"):
        if not question.strip():
            st.warning("Please type something first.")
        else:
            try:
                res = requests.post(f"{API_URL}/chat", json={"mode": "ask", "content": question})
                if res.ok:
                    st.markdown(res.json()["reply"])
                else:
                    st.error(f"Error {res.status_code}: Could not get a reply.")
            except Exception as e:
                st.error(f"Request failed: {e}")

# ---------------------------
# 📝 Code tab
# ---------------------------
with tab_code:
    st.subheader("Roast my code")
    st.markdown("Paste Python code. I’ll roast it, then explain it nicely.")
    code = st.text_area("Your Python code:", height=200, key="code_input")

    if st.button("Roast Me", key="code_btn"):
        if not code.strip():
            st.warning("Please paste your code first.")
        else:
            try:
                res = requests.post(f"{API_URL}/chat", json={"mode": "code", "content": code})
                if res.ok:
                    st.markdown(res.json()["reply"])
                else:
                    st.error(f"Error {res.status_code}: Could not get a roast.")
            except Exception as e:
                st.error(f"Request failed: {e}")

# ---------------------------
# 🎯 Quiz tab
# ---------------------------
with tab_quiz:
    st.subheader("Quiz time")
    st.markdown("Click **New Question**, pick an answer, then **Submit**. I’ll keep score.")

    cols = st.columns([1, 1, 2])
    if cols[0].button("🆕 New Question", key="quiz_new_btn"):
        try:
            res = requests.post(f"{API_URL}/chat", json={"mode": "quiz"})
            if res.ok:
                st.session_state.quiz_data = res.json()["reply"]
            else:
                st.error(f"Error {res.status_code}: Could not load quiz.")
        except Exception as e:
            st.error(f"Request failed: {e}")

    quiz = st.session_state.quiz_data

    if quiz:
        st.markdown(f"**Q:** {quiz['question']}")
        if quiz.get("code"):
            st.code(quiz["code"], language="python")

        choice = st.radio("Choose an answer:", quiz["options"], index=None, key="quiz_choice")

        if st.button("✅ Submit Answer", key="quiz_submit_btn"):
            if choice is None:
                st.warning("Please select an option before submitting.")
            else:
                st.session_state.quiz_stats["total"] += 1
                correct_answer = quiz["options"][quiz["answer"]]
                if choice == correct_answer:
                    st.success("Correct! 🎉")
                    st.session_state.quiz_stats["correct"] += 1
                    st.session_state.quiz_stats["score"] += quiz["score"]
                else:
                    st.error(f"Wrong! Correct answer: {correct_answer}")
                    # Ask backend for a roast
                    try:
                        roast_res = requests.post(
                            f"{API_URL}/roast",
                            json={
                                "question": quiz["question"],
                                "user_answer": choice,
                                "correct_answer": correct_answer,
                            },
                        )
                        if roast_res.ok:
                            st.markdown(roast_res.json().get("roast", ""))
                    except Exception as e:
                        st.info(f"(Roast unavailable) {e}")

        # Next question shortcut
        if st.button("➡️ Next Question", key="quiz_next_btn"):
            try:
                res = requests.post(f"{API_URL}/chat", json={"mode": "quiz"})
                if res.ok:
                    st.session_state.quiz_data = res.json()["reply"]
                    # clear selection for the new question
                    st.session_state.pop("quiz_choice", None)
                else:
                    st.error(f"Error {res.status_code}: Could not load quiz.")
            except Exception as e:
                st.error(f"Request failed: {e}")

        # Stats
        stats = st.session_state.quiz_stats
        st.markdown("---")
        st.markdown(
            f"**Score:** {stats['score']} points &nbsp;|&nbsp; "
            f"**Correct:** {stats['correct']} / {stats['total']}"
        )