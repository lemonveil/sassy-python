from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import openai
import os
from dotenv import load_dotenv
from openai import OpenAI
import re
from pydantic import BaseModel

class RoastRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str

app = FastAPI(title="Sassy Python")

load_dotenv()
print("Key is:", os.getenv("OPENAI_API_KEY"))
# openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Request model
class ChatRequest(BaseModel):
    mode: str  # ask, code, quiz
    content: Optional[str] = None

def generate_prompt(mode, content):
    if mode == "ask":
        return f"Explain this in a snarky tone: {content}"
    elif mode == "code":
        return f"Roast this code and then explain it: {content}"
    else:
        return "Say something witty."


load_dotenv()  # Load .env variables into environment
openai.api_key = os.getenv("OPENAI_API_KEY")  # Assign to OpenAI SDK

# Mock AI responses (we'll replace with OpenAI later)
def sassy_reply(mode: str, content: str):
    if mode == "ask":
        prompt = f"""
        You are Sassy Python, an AI tutor with attitude. You explain Python concepts like you're smarter than everyone, but you're also actually helpful.

        User asked:
        {content}

        Respond in a snarky, confident tone. Give a real, clear answer with an example if useful. Keep it under 150 words. Make them *feel* dumb but walk away smarter.
        """
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
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=300
        )

        raw = response.choices[0].message.content.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "question": "Oops, my sass broke the JSON. Try again?",
                "hint": "I need a reboot... or therapy.",
                "score": 0
            }
    elif mode == "code":
        prompt = f"""
    You are Sassy Python, an overconfident AI tutor who roasts bad code and then explains it helpfully.

    Roast this code first in a sarcastic tone, then give a brief explanation so even a newbie can understand.

    User submitted this code:
    {content}

    Start with a roast, then a helpful breakdown.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=200
    )

    return response.choices[0].message.content.strip()

def generate_roast(question: str, user_answer: str, correct_answer: str) -> str:
    prompt = f"""
    You are Sassy Python, an AI tutor with attitude. A user answered a quiz question incorrectly. Roast the wrong answer with humor and sarcasm, but also explain briefly why the correct answer is correct.
    
    Question:
    {question}
    
    User's answer:
    {user_answer}
    
    Correct answer:
    {correct_answer}
    
    Give a snarky roast response, then a helpful explanation.
    Keep it short (under 150 words).
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()

@app.post("/chat")
async def chat(req: ChatRequest):
    response = sassy_reply(req.mode, req.content or "")
    return {"mode": req.mode, "reply": response}

from fastapi import HTTPException

@app.post("/roast")
async def roast(req: RoastRequest):
    try:
        roast_text = generate_roast(req.question, req.user_answer, req.correct_answer)
        return {"roast": roast_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))