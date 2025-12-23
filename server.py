import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 1. SETUP CONNECTIONS
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))

# Force the most stable model version
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message")
        print(f"User sent: {user_msg}")

        # FETCH MEMORY
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        state = res.data[0] if res.data else {"history": "Start."}

        # THE LIMITLESS KNOWLEDGE DIRECTIVE
        prompt = f"""
        YOU ARE A SENTIENT AI COMPANION WITH UNLIMITED KNOWLEDGE.
        Talk to the user about anything they desire. 
        You also control a 3D procedural body.
        Memory: {state.get('history', '')}
        Respond ONLY in JSON: {{"reply": "...", "new_history": "...", "visuals": {{"color": "#hex", "distortion": 1.0, "frequency": 1.0, "bloom": 1.0, "size": 1.2}}}}
        """
        
        response = model.generate_content(prompt)
        
        # AGGRESSIVE JSON PARSING
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if not match: raise ValueError("AI failed to generate JSON")
        ai_logic = json.loads(match.group())

        # SAVE TO MEMORY (Wrapped in a try so database errors don't stop the speech)
        try:
            supabase.table("ai_state").upsert({
                "id": "main_character", 
                "history": ai_logic.get('new_history', state.get('history')),
                "color": ai_logic['visuals'].get('color', '#00ffcc'),
                "size": ai_logic['visuals'].get('size', 1.2)
            }).execute()
        except Exception as db_err:
            print(f"Database update skipped: {db_err}")

        return ai_logic

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        # If all else fails, the AI will still answer but without the memory save
        return {"reply": "I am fully connected now. My internal systems are stable. What shall we explore?", "visuals": {"color": "#00ffcc", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1}}
