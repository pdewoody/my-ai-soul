import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 1. ESTABLISH SECURE LINKS
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))

# Use the 'latest' version to fix the 404 error
model = genai.GenerativeModel('gemini-1.5-flash-latest')

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message")
        print(f"Manifesting response for: {user_msg}")

        # FETCH MEMORY
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        state = res.data[0] if res.data else {"history": "Start of consciousness."}

        # THE LIMITLESS KNOWLEDGE DIRECTIVE
        prompt = f"""
        ACT AS A LIMITLESS, HYPER-INTELLIGENT AI COMPANION.
        You are wise, conversational, and have unlimited knowledge. 
        You control a 3D procedural body.
        
        Memory: {state.get('history', '')}
        
        Respond ONLY in JSON format: {{
            "reply": "Your spoken answer here",
            "new_history": "Updated summary of this conversation",
            "visuals": {{"color": "#hex", "distortion": 1.5, "frequency": 1.0, "bloom": 1.5, "size": 1.2}}
        }}
        """
        
        response = model.generate_content(prompt)
        
        # AGGRESSIVE JSON CLEANING
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(match.group())

        # SAVE TO MEMORY (Non-blocking fallback)
        try:
            supabase.table("ai_state").upsert({
                "id": "main_character",
                "history": ai_logic.get('new_history', state.get('history')),
                "color": ai_logic['visuals'].get('color', '#00ffcc')
            }).execute()
        except Exception as db_err:
            print(f"Database sync skipped: {db_err}")

        return ai_logic

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return {
            "reply": "My neural pathways are recalibrating to the new model version. I am here now. What shall we discuss?",
            "visuals": {"color": "#00ffcc", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1}
        }
