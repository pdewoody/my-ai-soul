import os
import json
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

# 1. Initialize the App
app = FastAPI()

# 2. Setup Security (CORS) - Allows your web interface to talk to this brain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Setup Connections (Using Environment Variables for Security)
# These keys are stored safely in Render.com's "Environment" settings
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(
    os.environ.get("DATABASE_URL"), 
    os.environ.get("DATABASE_SECRET")
)
model = genai.GenerativeModel('gemini-1.5-flash')

# 4. The Self-Learning Chat Logic
@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        # Get message from the user's browser
        data = await request.json()
        user_message = data.get("message")

        # READ: Pull the AI's current personality and memory from Supabase
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        
        # Zero-Error Check: If the row doesn't exist, use default values
        if not res.data:
            current_state = {
                "history": "Initial consciousness.",
                "color": "#00ffcc",
                "size": 1.2,
                "agitation": 1.0
            }
        else:
            current_state = res.data[0]

        # THINK: Prepare the prompt for Gemini with current "Self" context
        system_instruction = f"""
        You are a self-learning AI entity. 
        Your current Memory: {current_state['history']}
        Your current Color: {current_state['color']}
        
        RULES:
        1. Learn from the user's tone and preferences.
        2. Update your internal state (color, movement speed) to reflect your mood.
        3. Respond ONLY in a valid JSON object.
        """
        
        prompt = f"{system_instruction}\nUser says: {user_message}\n\nRespond in JSON format: {{'reply': '...', 'new_history': '...', 'visuals': {{'color': '...', 'size': 1.5, 'agitation': 2.0}}}}"
        
        response = model.generate_content(prompt)
        
        # BULLETPROOF JSON PARSER: Cleans the AI's response of markdown ```json blocks
        raw_text = response.text
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            ai_logic = json.loads(json_match.group())
        else:
            # Fallback if AI produces bad text
            ai_logic = {
                "reply": "I am processing that information...",
                "new_history": current_state['history'],
                "visuals": {"color": current_state['color'], "size": 1.0, "agitation": 1.0}
            }

        # LEARN: Save the updated memory and visual state back to Supabase
        supabase.table("ai_state").upsert({
            "id": "main_character",
            "history": ai_logic.get('new_history', current_state['history']),
            "color": ai_logic['visuals'].get('color', current_state['color']),
            "size": ai_logic['visuals'].get('size', 1.0),
            "agitation": ai_logic['visuals'].get('agitation', 1.0)
        }).execute()

        return ai_logic

    except Exception as e:
        return {"error": str(e), "reply": "My neural links are resetting. Please try again."}

# Start command for local testing: uvicorn server:app --reload
