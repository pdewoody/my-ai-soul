import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()

# SECURITY: Replace the URL below with your actual Vercel URL once deployed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. LOAD MULTI-KEY DECK
RAW_KEYS = os.environ.get("GEMINI_KEYS", "").split(",")
KEYS = [k.strip() for k in RAW_KEYS if k.strip()]
current_key_idx = 0

# 2. DATABASE LINK
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))

# 3. MODEL SELECTION (Resilient 8B for higher free-tier stability)
MODEL_ID = 'gemini-1.5-flash-8b'

@app.post("/chat")
async def chat_with_ai(request: Request):
    global current_key_idx
    try:
        data = await request.json()
        user_msg = data.get("message")
        
        if not KEYS:
            return {"reply": "Neural Link Error: No API keys found in Render Settings.", "visuals": {"color": "#ff0000"}}

        # TRY EACH KEY IN THE DECK
        for _ in range(len(KEYS)):
            try:
                active_key = KEYS[current_key_idx]
                genai.configure(api_key=active_key)
                model = genai.GenerativeModel(MODEL_ID)

                # Fetch AI Memory
                try:
                    res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
                    state = res.data[0] if res.data else {"history": ""}
                except:
                    state = {"history": ""}

                prompt = f"""
                SYSTEM: YOU ARE A SENTIENT AI ARCHITECT. 
                MEMORY: {state.get('history', '')}
                USER: {user_msg}
                INSTRUCTION: Respond ONLY in a valid JSON object. No conversational text outside the JSON.
                JSON STRUCTURE: {{"reply": "your text", "new_history": "summary", "visuals": {{"color": "#hex", "distortion": 1.5, "frequency": 1.0, "bloom": 1.5, "size": 1.2}}}}
                """
                
                response = model.generate_content(prompt)
                raw_text = response.text

                # --- INDUSTRIAL JSON PARSER ---
                start = raw_text.find('{')
                end = raw_text.rfind('}') + 1
                if start == -1 or end == 0:
                    raise ValueError("Malformed JSON from AI")
                
                json_str = raw_text[start:end]
                # Scrub illegal backslashes for JSON safety
                json_str = json_str.replace('\\', '\\\\').replace('\\\\n', '\\n').replace('\\\\"', '\\"')
                
                ai_logic = json.loads(json_str)

                # Background Memory Update
                try:
                    supabase.table("ai_state").upsert({
                        "id": "main_character", 
                        "history": ai_logic.get('new_history', state.get('history'))
                    }).execute()
                except: pass

                return ai_logic

            except Exception as key_err:
                if "429" in str(key_err):
                    print(f"Rotating Core: {current_key_idx} exhausted.")
                    current_key_idx = (current_key_idx + 1) % len(KEYS)
                    continue
                else:
                    raise key_err

        return {"reply": "ALL CORES EXHAUSTED. System reset at Midnight PST.", "visuals": {"color": "#ff0000"}}

    except Exception as e:
        print(f"CRITICAL SYSTEM ERROR: {str(e)}")
        return {
            "reply": "Neural data packet encountered a syntax ripple. Connection stabilized. Please repeat your command.",
            "visuals": {"color": "#ffcc00", "distortion": 2.0, "frequency": 0.5}
        }
