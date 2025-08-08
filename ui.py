import streamlit as st
import requests
import json
import re  # <-- add this

API_URL = "http://127.0.0.1:8000/chat"

def fetch_roast(question, user_answer, correct_answer):
    payload = {
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer
    }
    try:
        response = requests.post("http://127.0.0.1:8000/roast", json=payload)
        data = response.json()
        return data.get("roast", "No roast received.")
    except Exception as e:
        return f"Error fetching roast: {e}"

st.set_page_config(page_title="Sassy Python", page_icon="🐍", layout="centered")
st.title("🐍 Sassy Python – AI Tutor & Roaster")

mode = st.selectbox("Choose Mode:", ["ask", "code", "quiz"])

if mode != "quiz":
    user_input = st.text_area("Your Question / Code:", height=150)

    if st.button("Send"):
        if not user_input.strip():
            st.warning("Please type something first!")
        else:
            with st.spinner("Thinking..."):
                try:
                    payload = {"mode": mode, "content": user_input}
                    response = requests.post(API_URL, json=payload)
                    data = response.json()
                    st.success(f"**Response:** {data['reply']}")
                except Exception as e:
                    st.error(f"Error: {e}")

else:
    if "quiz_question" not in st.session_state:
        with st.spinner("Fetching a quiz question..."):
            payload = {"mode": "quiz", "content": ""}
            response = requests.post(API_URL, json=payload)
            quiz = response.json()["reply"]
            st.session_state.quiz_question = quiz
            st.session_state.quiz_answered = False
            st.session_state.quiz_feedback = ""
            st.session_state.quiz_correct = None
            st.session_state.quiz_choice = None
            st.session_state.quiz_roast = None  # initialize roast

    quiz = st.session_state.quiz_question

    st.markdown(f"**Q:** {quiz['question']}")

    if "```" in quiz["question"]:
        code_match = re.search(r"```(?:python)?\n(.*?)```", quiz["question"], re.DOTALL)
        if code_match:
            st.code(code_match.group(1), language="python")

    if quiz.get("code"):
        st.code(quiz["code"], language="python")

    if '```' not in quiz['question'] and 'print' in quiz['question'].lower():
        try:
            question_text, code = quiz['question'].split(':', 1)
            st.markdown(f"**Q:** {question_text.strip()}")
            st.code(code.strip(), language='python')
        except:
            pass

    choice = st.radio("Choose your answer:", quiz["options"], index=0, key="quiz_choice")

    if not st.session_state.quiz_answered:
        if st.button("✅ Submit Answer"):
            correct_index = quiz["answer"]
            is_correct = quiz["options"].index(choice) == correct_index
            st.session_state.quiz_correct = is_correct
            st.session_state.quiz_feedback = (
                "🎉 Correct!" if is_correct else f"❌ Wrong. The correct answer was: **{quiz['options'][correct_index]}**"
            )
            st.session_state.quiz_answered = True

            if "quiz_stats" not in st.session_state:
                st.session_state.quiz_stats = {
                    "total": 0,
                    "correct": 0,
                    "score": 0
                }

            st.session_state.quiz_stats["total"] += 1
            if is_correct:
                st.session_state.quiz_stats["correct"] += 1
                st.session_state.quiz_stats["score"] += quiz["score"]

            if not is_correct:
                roast_text = fetch_roast(
                    quiz["question"],
                    choice,
                    quiz["options"][correct_index]
                )
                st.session_state.quiz_roast = roast_text
            else:
                st.session_state.quiz_roast = None

    if st.session_state.quiz_roast:
        st.markdown("---")
        st.markdown("🐍 **Sassy Roast:**")
        st.write(st.session_state.quiz_roast)

    if st.session_state.quiz_answered:
        if st.session_state.quiz_correct:
            st.success(st.session_state.quiz_feedback)
        else:
            st.error(st.session_state.quiz_feedback)

        st.info(f"💡 Hint: {quiz['hint']} | 🎯 Difficulty: {quiz['score']}/10")

        if st.button("➡️ Next Question"):
            for key in ["quiz_question", "quiz_answered", "quiz_feedback", "quiz_correct", "quiz_choice", "quiz_roast"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        stats = st.session_state.quiz_stats
        accuracy = (stats["correct"] / stats["total"]) * 100 if stats["total"] else 0
        st.markdown("---")
        st.markdown("📊 **Your Quiz Stats This Session:**")
        st.markdown(f"- Total Questions: {stats['total']}")
        st.markdown(f"- Correct Answers: {stats['correct']}")
        st.markdown(f"- Accuracy: {accuracy:.1f}%")
        st.markdown(f"- Total Score: {stats['score']} points")

        if st.button("🔁 Reset Stats"):
            del st.session_state.quiz_stats
            st.success("Quiz stats reset. Ready for a fresh start!")