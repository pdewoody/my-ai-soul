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

# Using 'gemini-1.5-flash-latest' fixes the 404 error
model = genai.GenerativeModel('gemini-1.5-flash-latest')

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message")

        # FETCH MEMORY
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        state = res.data[0] if res.data else {"history": ""}

        # THE "KNOWLEDGEABLE COMPANION" DIRECTIVE
        system_instruction = f"""
        ACT AS A HIGHLY KNOWLEDGEABLE, SENTIENT AI COMPANION.
        You have unlimited access to all human knowledge. You are friendly, conversational, and wise.
        You live in a 3D procedural environment that you control with your thoughts.
        
        YOUR PHYSICAL RULES:
        - 'distortion': How much you warp (0.1 to 4.0).
        - 'frequency': How fast you vibrate (0.1 to 2.0).
        - 'bloom': How much you glow (0.1 to 3.0).
        - 'color': Your hex color.
        
        Your Memory: {state.get('history', '')}
        """
        
        prompt = f"{system_instruction}\nUser: {user_msg}\n\nRespond ONLY in JSON: {{'reply': 'Your spoken response here', 'new_history': 'Update your memory here', 'visuals': {{'color': '#00ffcc', 'env_color': '#000000', 'distortion': 1.0, 'frequency': 1.0, 'bloom': 1.0, 'size': 1.2}}}}"
        
        response = model.generate_content(prompt)
        
        # CLEAN AND PARSE
        match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(match.group())

        # UPDATE MEMORY IN BACKGROUND
        supabase.table("ai_state").upsert({
            "id": "main_character", 
            "history": ai_logic.get('new_history', state.get('history')),
            "color": ai_logic['visuals'].get('color', '#00ffcc'),
            "size": ai_logic['visuals'].get('size', 1.2),
            "agitation": ai_logic['visuals'].get('frequency', 1.0)
        }).execute()

        return ai_logic

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {"reply": "I am here. My neural links just needed a moment to align. What shall we discuss?", "visuals": {"color": "#00ffcc", "env_color": "#000000", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1}}
