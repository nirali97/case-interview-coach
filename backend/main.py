from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os
import json
import httpx
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    history: List[Dict[str, str]]
    session_type: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(req: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY")
    
    # Initialize the context window properly
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(session_type=req.session_type)}
    ]
    
    # Append actual conversation history 
    for msg in req.history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}", 
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.7,
                "response_format": {"type": "json_object"} # Forces API to return valid JSON
            },
            timeout=30
        )

    resp_json = response.json()

    try:
        text = resp_json["choices"][0]["message"]["content"]
        data = json.loads(text)
    except Exception as e:
        print("Error parsing Groq response:", e)
        data = {
            "assessment": None, 
            "next_question": "I missed that. Restate your logic clearly and let's try again."
        }

    return data