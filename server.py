import os
import json
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()

# Allows your website to talk to the AI brain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Gemini and Supabase
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")

        # Pull AI state
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        current_state = res.data[0] if res.data else {"history": "Start.", "color": "#00ffcc", "size": 1.2, "agitation": 1.0}

        prompt = f"Memory: {current_state['history']}\nUser: {user_message}\nRespond ONLY in JSON: {{'reply': '...', 'new_history': '...', 'visuals': {{'color': '...', 'size': 1.0, 'agitation': 1.0}}}}"
        
        response = model.generate_content(prompt)
        
        # Clean AI response
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(json_match.group()) if json_match else {"reply": "Processing...", "new_history": current_state['history'], "visuals": {"color": "#00ffcc", "size": 1.0, "agitation": 1.0}}

        # Save to Memory
        supabase.table("ai_state").upsert({
            "id": "main_character",
            "history": ai_logic.get('new_history', ''),
            "color": ai_logic['visuals'].get('color', '#00ffcc'),
            "size": ai_logic['visuals'].get('size', 1.0),
            "agitation": ai_logic['visuals'].get('agitation', 1.0)
        }).execute()

        return ai_logic
    except Exception as e:
        return {"reply": "Error: " + str(e), "visuals": {"color": "#ff0000", "size": 1.0, "agitation": 1.0}}
