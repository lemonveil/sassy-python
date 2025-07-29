from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional
import random

app = FastAPI(title="Sassy Python")

# Request model
class ChatRequest(BaseModel):
    mode: str  # ask, code, quiz
    content: Optional[str] = None

# Mock AI responses (we'll replace with OpenAI later)
def sassy_reply(mode: str, content: str):
    if mode == "ask":
        return f"Ugh, fine. Here's your answer: '{content}' is basically obvious, but okay..."
    elif mode == "code":
        return f"Your code smells... Let me explain why: {content[:50]}..."
    elif mode == "quiz":
        question = f"What is the output of `print(2+2)`?"
        return {
            "question": question,
            "hint": "Come on, even my pet snake knows this.",
            "score": random.randint(0, 10)
        }
    else:
        return "Pick a mode: ask, code, or quiz. Duh."


@app.post("/chat")
async def chat(req: ChatRequest):
    response = sassy_reply(req.mode, req.content or "")
    return {"mode": req.mode, "reply": response}
