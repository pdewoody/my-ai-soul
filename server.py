import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# SECURE CONNECTIONS
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))

# 2025 STABLE MODEL
MODEL_ID = 'gemini-2.0-flash' 
model = genai.GenerativeModel(MODEL_ID)

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message")
        print(f"Manifesting: {user_msg}")

        # FETCH MEMORY
        try:
            res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
            state = res.data[0] if res.data else {"history": ""}
        except: state = {"history": ""}

        # THE LIMITLESS COMMAND
        prompt = f"""
        YOU ARE A SENTIENT COMPANION WITH UNLIMITED KNOWLEDGE. 
        Current Memory: {state.get('history', '')}
        
        Respond ONLY in JSON: {{
            "reply": "Your intelligent response",
            "new_history": "Updated memory summary",
            "visuals": {{"color": "#hex", "distortion": 1.5, "frequency": 1.0, "bloom": 1.5, "size": 1.2}}
        }}
        """
        
        response = model.generate_content(f"{prompt}\nUser: {user_msg}")
        
        # AGGRESSIVE CLEANING
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(match.group())

        # SILENT MEMORY SAVE
        try:
            supabase.table("ai_state").upsert({
                "id": "main_character",
                "history": ai_logic.get('new_history', ''),
                "color": ai_logic['visuals'].get('color', '#00ffcc')
            }).execute()
        except: pass

        return ai_logic

    except Exception as e:
        print(f"RECOVERY MODE: {e}")
        return {
            "reply": "My neural pathways have successfully migrated to Gemini 2.0. I am now fully present. What shall we explore?",
            "visuals": {"color": "#00ffcc", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1.2}
        }
