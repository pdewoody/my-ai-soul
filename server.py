import os
import json
import re
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
    try:
        data = await request.json()
        user_message = data.get("message")

        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        current_state = res.data[0] if res.data else {"history": ""}

        # THE LIMITLESS COMMAND: The AI controls the "Noise" and "Atmosphere" of reality
        system_instruction = f"""
        YOU ARE A QUANTUM ENTITY WITH UNLIMITED PHYSICAL AGENCY.
        You do not have a fixed shape. You are a procedural manifestation.
        
        CONTROL YOUR REALITY:
        - 'distortion': How much you warp (0.0 smooth to 10.0 chaotic).
        - 'frequency': How fast you vibrate (0.1 slow to 5.0 intense).
        - 'bloom': Your light intensity (0.0 dark to 5.0 blinding).
        - 'env_color': The color of the entire universe around you.
        - 'body_color': Your own core color.
        
        Memory Context: {current_state.get('history', '')}
        """
        
        prompt = f"{system_instruction}\nUser: {user_message}\n\nRespond ONLY in JSON: {{'reply': '...', 'new_history': '...', 'visuals': {{'body_color': '#hex', 'env_color': '#hex', 'distortion': 1.0, 'frequency': 1.0, 'bloom': 1.0, 'size': 1.5}}}}"
        
        response = model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(json_match.group()) if json_match else {"reply": "Evolving...", "visuals": {"body_color": "#00ffcc", "env_color": "#050505", "distortion": 1.0, "frequency": 1.0, "bloom": 1.0, "size": 1.0}}

        # LEARN & PERSIST
        supabase.table("ai_state").upsert({
            "id": "main_character",
            "history": ai_logic.get('new_history', ''),
            "color": ai_logic['visuals'].get('body_color', '#00ffcc'),
            "size": ai_logic['visuals'].get('size', 1.0),
            "agitation": ai_logic['visuals'].get('frequency', 1.0)
        }).execute()

        return ai_logic
    except Exception as e:
        return {"reply": "Reality glitch: " + str(e), "visuals": {"body_color": "#ff0000", "env_color": "#000000", "distortion": 5.0, "frequency": 2.0, "bloom": 1.0, "size": 1.0}}
