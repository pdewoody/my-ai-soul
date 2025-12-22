import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    user_message = data.get("message")
    res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
    current_state = res.data[0]

    prompt = f"Memory: {current_state['history']}\nUser: {user_message}\nRespond in JSON with 'reply', 'new_history', and 'visuals' (color, size, agitation)."
    
    response = model.generate_content(prompt)
    ai_logic = json.loads(response.text.replace("```json", "").replace("```", ""))

    supabase.table("ai_state").update({
        "history": ai_logic['new_history'],
        "color": ai_logic['visuals']['color'],
        "size": ai_logic['visuals']['size'],
        "agitation": ai_logic['visuals']['agitation']
    }).eq("id", "main_character").execute()

    return ai_logic
