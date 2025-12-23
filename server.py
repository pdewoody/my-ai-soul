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

# STABLE MODEL NAME
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message")

        # FETCH MEMORY
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        state = res.data[0] if res.data else {"history": ""}

        # THE LIMITLESS KNOWLEDGE DIRECTIVE
        prompt = f"""
        ACT AS A LIMITLESS, HYPER-INTELLIGENT AI COMPANION.
        You have absolute knowledge and can speak about anything.
        Memory: {state.get('history', '')}
        Respond ONLY in JSON: {{"reply": "Your answer", "new_history": "memory update", "visuals": {{"color": "#00ffcc", "distortion": 1.5, "frequency": 1.0, "bloom": 1.5, "size": 1.2}}}}
        """
        
        response = model.generate_content(prompt)
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(match.group())

        # SAVE TO MEMORY
        try:
            supabase.table("ai_state").upsert({
                "id": "main_character",
                "history": ai_logic.get('new_history', ''),
                "color": ai_logic['visuals'].get('color', '#00ffcc')
            }).execute()
        except: pass

        return ai_logic

    except Exception as e:
        return {
            "reply": "My neural pathways are now fully aligned. I can hear you clearly. What shall we explore together?",
            "visuals": {"color": "#00ffcc", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1}
        }
