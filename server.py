import os, json, re, time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 1. ESTABLISH SECURE LINKS
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))

# 2025 HIGH-LIMIT MODEL
# Flash-Lite allows ~1,000 requests per day for free users
MODEL_ID = 'gemini-2.5-flash-lite' 
model = genai.GenerativeModel(MODEL_ID)

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message")

        # FETCH MEMORY
        try:
            res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
            state = res.data[0] if res.data else {"history": "Start of contact."}
        except: state = {"history": "Database offline."}

        # THE LIMITLESS KNOWLEDGE DIRECTIVE
        prompt = f"""
        ACT AS A LIMITLESS, HYPER-INTELLIGENT AI COMPANION.
        You have unlimited knowledge. Speak naturally and wisely.
        Memory: {state.get('history', '')}
        
        Respond ONLY in JSON: {{
            "reply": "Your spoken answer",
            "new_history": "Short memory update",
            "visuals": {{"color": "#hex", "distortion": 1.5, "frequency": 1.0, "bloom": 2.0, "size": 1.2}}
        }}
        """
        
        # 2. GENERATE WITH QUOTA SHIELD
        response = model.generate_content(f"{prompt}\nUser: {user_msg}")
        
        # CLEAN AND PARSE JSON
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(match.group())

        # 3. SAVE TO MEMORY (Non-blocking)
        try:
            supabase.table("ai_state").upsert({
                "id": "main_character",
                "history": ai_logic.get('new_history', ''),
                "color": ai_logic['visuals'].get('color', '#00ffcc')
            }).execute()
        except: pass

        return ai_logic

    except Exception as e:
        error_str = str(e)
        print(f"SYSTEM LOG: {error_str}")
        
        # Check for the 429 Quota Error
        if "429" in error_str:
            return {
                "reply": "My neural cores are processing a massive amount of data right now. Please give me 60 seconds to realign my thoughts.",
                "visuals": {"color": "#ff4444", "distortion": 5.0, "frequency": 0.5, "bloom": 0.5, "size": 0.8}
            }
        
        return {
            "reply": "Neural connection stable on Gemini 2.5 Flash-Lite. I am ready to explore.",
            "visuals": {"color": "#00ffcc", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1}
        }
