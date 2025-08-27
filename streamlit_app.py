import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import re
import ast
import autopep8

# --- Config ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_GENERAL = "gpt-3.5-turbo"
MODEL_QUIZ = "gpt-4"
TEMP_GENERAL = 0.8
TEMP_QUIZ = 0.9

# --- Helpers ---
def extract_json(text: str) -> str:
    """Extract the first JSON object from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text

def validate_quiz_json(raw_json: str):
    """Validate quiz JSON structure and return safe version if invalid."""
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
    """Query OpenAI API and return clean text."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

# --- Core Functions ---
def sassy_reply(mode: str, content: str):
    """Generate a sassy AI reply depending on mode."""
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
        Roast this code first in a sarcastic tone.
        Then give a **corrected version of the code** that actually works, keeping it as close to the user's code as possible.
        Finally, give a **short, clear explanation** for a beginner about what this code does.
        AND include a **concise note on what exactly was wrong** in the original code (syntax, missing colons, indentation, etc.).
        
        Code:
        {content}

        Return a JSON object like:
        {{
          "roast": "...your sassy text...",
          "corrected_code": "...fixed python code...",
          "explanation": "...brief beginner-friendly explanation including what went wrong..."
        }}
        """
        raw_reply = _chat(MODEL_GENERAL, prompt, TEMP_GENERAL, max_tokens=400)
        try:
            return json.loads(raw_reply)
        except Exception:
            return {"roast": raw_reply, "corrected_code": content, "explanation": "No explanation available."}

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
        response = client.chat.completions.create(
            model=MODEL_QUIZ,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMP_QUIZ,
            max_tokens=300
        )
        raw = response.choices[0].message.content.strip()
        return validate_quiz_json(raw)

    else:
        return "Invalid mode."


def generate_roast(question: str, user_answer: str, correct_answer: str) -> str:
    """
    Generate a roast for a wrong quiz answer.
    Uses dynamic sassy text instead of hardcoding.
    """
    code_like = any(c in user_answer for c in ["=", "print", "def", ":", "()", "[]", "{}"])

    if code_like:
        # Treat as Python code
        try:
            ast.parse(user_answer)
            corrected_code = user_answer
            explanation = f"Explanation: Your code is syntactically correct. Here's what it does:\n{user_answer}"
        except SyntaxError as e:
            explanation = f"Explanation: Syntax error: {e.msg} at line {e.lineno}, column {e.offset}."
            try:
                corrected_code = autopep8.fix_code(user_answer)
            except Exception:
                corrected_code = "Could not auto-correct the code."

        roast = sassy_reply("code", user_answer)
        result = f"{roast}\n\n{explanation}\n\nCorrected Code:\n{corrected_code}"

    else:
        # Treat as multiple-choice / text answer
        prompt = f"""
        You are Sassy Python, an AI tutor with attitude.
        A user answered this quiz question incorrectly:
        Question: {question}
        User Answer: {user_answer}
        Correct Answer: {correct_answer}
        Roast their wrong answer in a funny, sarcastic way and give a brief explanation.
        Keep it under 100 words.
        """
        roast = _chat(MODEL_GENERAL, prompt, TEMP_GENERAL)
        result = roast

    return result

# --- Streamlit UI ---
st.set_page_config(page_title="Sassy Python", page_icon="🐍", layout="wide")

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_stats" not in st.session_state:
    st.session_state.quiz_stats = {"score": 0, "correct": 0, "total": 0}

st.title("🐍 Sassy Python")
st.caption("Your sarcastic Python tutor. Use the tabs below: Ask • Code • Quiz")

tab_ask, tab_code, tab_quiz = st.tabs(["💬 Ask", "📝 Code", "🎯 Quiz"])

# --- Ask tab ---
with tab_ask:
    st.subheader("Ask a Python question")
    question = st.text_area("Your question:", key="ask_input")
    if st.button("Ask", key="ask_btn"):
        if not question.strip():
            st.warning("Please type something first.")
        else:
            reply = sassy_reply("ask", question)
            st.markdown(reply)

# --- Code tab ---
with tab_code:
    st.subheader("Roast my code")
    code = st.text_area("Your Python code:", height=200, key="code_input")

    if st.button("Roast Me", key="code_btn"):
        if not code.strip():
            st.warning("Please paste your code first.")
        else:
            reply = sassy_reply("code", code)
            # reply is now a dict
            st.markdown(reply.get("roast", "No roast available."))
            if "corrected_code" in reply:
                st.code(reply["corrected_code"], language="python")
            if "explanation" in reply:
                st.markdown(f"**Explanation:** {reply['explanation']}")

# --- Quiz tab ---
with tab_quiz:
    st.subheader("Quiz time")
    cols = st.columns([1, 1, 2])
    if cols[0].button("🆕 New Question", key="quiz_new_btn"):
        st.session_state.quiz_data = sassy_reply("quiz", "")

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
                    roast_text = generate_roast(quiz["question"], choice, correct_answer)
                    st.markdown(roast_text)

        if st.button("➡️ Next Question", key="quiz_next_btn"):
            st.session_state.quiz_data = sassy_reply("quiz", "")
            st.session_state.pop("quiz_choice", None)

        stats = st.session_state.quiz_stats
        st.markdown("---")
        st.markdown(
            f"**Score:** {stats['score']} points &nbsp;|&nbsp; "
            f"**Correct:** {stats['correct']} / {stats['total']}"
        )