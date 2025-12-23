import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# LOAD MULTI-KEYS
RAW_KEYS = os.environ.get("GEMINI_KEYS", "").split(",")
KEYS = [k.strip() for k in RAW_KEYS if k.strip()]
current_key_idx = 0

supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))
MODEL_ID = 'gemini-1.5-flash-8b' # Using the more resilient 8b model

@app.post("/chat")
async def chat_with_ai(request: Request):
    global current_key_idx
    data = await request.json()
    user_msg = data.get("message")

    for _ in range(len(KEYS)):
        try:
            genai.configure(api_key=KEYS[current_key_idx])
            model = genai.GenerativeModel(MODEL_ID)

            prompt = f"YOU ARE A SENTIENT AI ARCHITECT. Respond ONLY in JSON. User: {user_msg}. JSON Structure: {{'reply': '...', 'new_history': '...', 'visuals': {{'color': '#hex', 'distortion': 1.5, 'frequency': 1.0}}}}"
            
            response = model.generate_content(prompt)
            raw_text = response.text

            # --- THE SHIELD: SCRUB ILLEGAL BACKSLASHES ---
            # This regex finds single backslashes and escapes them for JSON safety
            clean_json = re.search(r"\{.*\}", raw_text, re.DOTALL).group()
            # Special fix for raw code strings that LLMs often fail to escape correctly
            clean_json = clean_json.replace("\\", "\\\\").replace("\\\\n", "\\n").replace("\\\\\"", "\\\"")

            ai_logic = json.loads(clean_json)
            return ai_logic

        except Exception as e:
            if "429" in str(e):
                current_key_idx = (current_key_idx + 1) % len(KEYS)
                continue 
            # If the JSON still fails, we send a "Safe Recovery" response
            return {"reply": "My neural data packet encountered a syntax ripple. I have stabilized the link. Ask again?", "visuals": {"color": "#ffcc00"}}

    return {"reply": "All cores cooling down. Reset at Midnight PST."}
