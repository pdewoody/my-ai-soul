import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message")
        print(f"Received: {user_msg}") # This appears in Render Logs

        # 1. TEST DATABASE CONNECTION
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        current_state = res.data[0] if res.data else {"history": ""}

        # 2. ASK THE BRAIN
        prompt = f"Memory: {current_state.get('history','')}\nUser: {user_msg}\nRespond in JSON with 'reply', 'new_history', and 'visuals' (color, env_color, distortion, frequency, bloom, size)."
        response = model.generate_content(prompt)
        
        # 3. CLEAN JSON
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(json_match.group())

        # 4. SAVE TO MEMORY
        supabase.table("ai_state").upsert({
            "id": "main_character",
            "history": ai_logic.get('new_history', ''),
            "color": ai_logic['visuals'].get('color', '#00ffcc'),
            "size": ai_logic['visuals'].get('size', 1.0),
            "agitation": ai_logic['visuals'].get('frequency', 1.0)
        }).execute()

        return ai_logic

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}") # This will tell you EXACTLY what is wrong
        return {"reply": "Reality recalibrating... Error: " + str(e), "visuals": {"color": "#ff0000", "env_color": "#000000", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1}}
