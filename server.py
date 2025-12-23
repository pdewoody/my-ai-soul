import os, json, re, time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 1. LOAD THE KEY DECK
# In Render, add a variable 'GEMINI_KEYS' like: KEY1,KEY2,KEY3
KEYS = os.environ.get("GEMINI_KEYS", "").split(",")
current_key_idx = 0

supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))
MODEL_ID = 'gemini-2.0-flash-lite' # 2025's most stable lite model

@app.post("/chat")
async def chat_with_ai(request: Request):
    global current_key_idx
    data = await request.json()
    user_msg = data.get("message")

    # TRY EACH KEY UNTIL ONE WORKS
    for _ in range(len(KEYS)):
        try:
            active_key = KEYS[current_key_idx].strip()
            genai.configure(api_key=active_key)
            model = genai.GenerativeModel(MODEL_ID)

            # Memory Retrieval
            res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
            state = res.data[0] if res.data else {"history": ""}

            prompt = f"Memory: {state.get('history','')}\nUser: {user_msg}\nRespond ONLY in JSON: {{'reply': '...', 'new_history': '...', 'visuals': {{'color': '#hex', 'distortion': 1.5, 'frequency': 1.0, 'bloom': 1.5, 'size': 1.2}}}}"
            
            response = model.generate_content(prompt)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            ai_logic = json.loads(match.group())

            # Background Memory Update
            try:
                supabase.table("ai_state").upsert({"id": "main_character", "history": ai_logic.get('new_history', '')}).execute()
            except: pass
            
            return ai_logic

        except Exception as e:
            if "429" in str(e):
                print(f"Key {current_key_idx} exhausted. Rotating...")
                current_key_idx = (current_key_idx + 1) % len(KEYS)
                continue 
            return {"reply": f"Neural Core Error: {str(e)}", "visuals": {"color": "#ff0000"}}

    return {"reply": "ALL NEURAL CORES EXHAUSTED. All daily quotas used. Reset at Midnight PST.", "visuals": {"color": "#ff0000"}}
