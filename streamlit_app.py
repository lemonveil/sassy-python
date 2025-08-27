# sassy_python.py
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import re

# --- Load API Key ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Model Config ---
MODEL_GENERAL = "gpt-3.5-turbo"
MODEL_QUIZ = "gpt-4"
TEMP_GENERAL = 0.8
TEMP_QUIZ = 0.9

# --- Streamlit Page Config ---
st.set_page_config(page_title="Sassy Python", layout="centered")
st.title("🐍 Sassy Python")
st.caption("Your sarcastic Python tutor")

# --- Session State ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_stats" not in st.session_state:
    st.session_state.quiz_stats = {"score": 0, "correct": 0, "total": 0}

# --- Helper Functions ---
def extract_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text

def validate_quiz_json(raw_json: str):
    fallback = {
        "question": "Oops, my sass broke the quiz format. Try again?",
        "code": None,
        "options": ["Python", "Monty", "Coffee", "I give up"],
        "answer": 0,
        "hint": "I need a reboot... or coffee.",
        "score": 1
    }
    try:
        raw_json = extract_json(raw_json)
        quiz = json.loads(raw_json)

        required_keys = ["question", "options", "answer", "hint", "score"]
        if not all(key in quiz for key in required_keys):
            return fallback
        if not isinstance(quiz["options"], list) or not all(isinstance(opt, str) for opt in quiz["options"]):
            return fallback
        if not isinstance(quiz["answer"], int):
            return fallback
        if not isinstance(quiz["score"], int):
            return fallback
        if "code" in quiz and not (quiz["code"] is None or isinstance(quiz["code"], str)):
            quiz["code"] = None
        return quiz
    except Exception:
        return fallback

def _chat(model: str, prompt: str, temperature: float, max_tokens: int = 200) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def sassy_reply(mode: str, content: str):
    if mode in ["ask", "code"] and not content:
        return "You forgot to give me something to sass about."

    if mode == "ask":
        prompt = f"""
        You are Sassy Python, an AI tutor with attitude.
        Explain this Python concept in a sarcastic, confident tone.
        Give a real, concise answer with an example if useful (max 150 words).

        Question:
        {content}
        """
        return _chat(MODEL_GENERAL, prompt, TEMP_GENERAL)

    elif mode == "code":
        prompt = f"""
        You are Sassy Python, an overconfident AI tutor.
        Roast this code first in a sarcastic tone, then give a short, clear explanation for a beginner.

        Code:
        {content}
        """
        return _chat(MODEL_GENERAL, prompt, TEMP_GENERAL)

    elif mode == "quiz":
        prompt = """
        You are Sassy Python, an AI that generates fun Python quiz questions.

        Task:
        - Generate a beginner or intermediate Python multiple-choice question.
        - If needed, include a short Python code snippet in a separate field.
        - Keep questions clear and concise.
        - Be mildly sarcastic but still educational.

        Return ONLY a JSON object like this:
        {
          "question": "What will the following code output?",
          "code": "print(2 ** 3)",   // Omit this field if not needed
          "options": [
            "6",
            "8",
            "9",
            "Error"
          ],
          "answer": 1,
          "hint": "Remember what ** means in Python.",
          "score": 3
        }
        """
        raw = _chat(MODEL_QUIZ, prompt, TEMP_QUIZ, max_tokens=300)
        return validate_quiz_json(raw)
    else:
        return "Invalid mode."

def generate_roast(question: str, user_answer: str, correct_answer: str) -> str:
    prompt = f"""
    You are Sassy Python, an AI tutor with attitude.
    A user answered a quiz question incorrectly.
    Roast their wrong answer with humor and sarcasm, then briefly explain the correct answer.

    Question:
    {question}

    User's Answer:
    {user_answer}

    Correct Answer:
    {correct_answer}

    Keep it under 150 words.
    """
    return _chat(MODEL_GENERAL, prompt, 0.85)

# --- Sidebar Mode Selector ---
mode = st.sidebar.selectbox("Choose Mode", ["ask", "code", "quiz"])

# --- Ask Mode ---
if mode == "ask":
    question = st.text_area("Ask Sassy Python a Python question:")
    if st.button("Ask"):
        if not question.strip():
            st.warning("Please type something first.")
        else:
            st.markdown(sassy_reply("ask", question))

# --- Code Mode ---
elif mode == "code":
    code = st.text_area("Paste your Python code for a roast + explanation:")
    if st.button("Roast Me"):
        if not code.strip():
            st.warning("Please paste your code first.")
        else:
            st.markdown(sassy_reply("code", code))

# --- Quiz Mode ---
elif mode == "quiz":
    if st.button("Get a New Question"):
        st.session_state.quiz_data = sassy_reply("quiz", "")

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
                roast_text = generate_roast(quiz["question"], choice, correct_answer)
                st.markdown(roast_text)

        st.markdown(f"**Score:** {st.session_state.quiz_stats['score']} points")
        st.markdown(f"**Correct Answers:** {st.session_state.quiz_stats['correct']} / {st.session_state.quiz_stats['total']}")