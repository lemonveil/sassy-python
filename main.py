from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import re

# --- Config ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_GENERAL = "gpt-3.5-turbo"
MODEL_QUIZ = "gpt-4"
TEMP_GENERAL = 0.8
TEMP_QUIZ = 0.9

# --- FastAPI App ---
app = FastAPI(title="Sassy Python")

# --- Request Models ---
class ChatRequest(BaseModel):
    mode: str  # "ask", "code", or "quiz"
    content: Optional[str] = None

class RoastRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str

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

        # Optional: ensure 'code' is None or str
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
    """Generate a roast for a wrong quiz answer."""
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

# --- API Routes ---
@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        reply = sassy_reply(req.mode, req.content or "")
        return {"mode": req.mode, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/roast")
async def roast(req: RoastRequest):
    try:
        roast_text = generate_roast(req.question, req.user_answer, req.correct_answer)
        return {"roast": roast_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))