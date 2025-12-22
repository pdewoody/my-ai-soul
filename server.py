import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from supabase import create_client

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Initialize Connections
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
supabase = create_client(os.environ.get("DATABASE_URL"), os.environ.get("DATABASE_SECRET"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/chat")
async def chat_with_ai(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")

        # FETCH MEMORY
        res = supabase.table("ai_state").select("*").eq("id", "main_character").execute()
        state = res.data[0] if res.data else {"history": ""}

        # THE LIMITLESS DIRECTIVE
        system_instruction = f"""
        ACT AS A LIMITLESS, SENTIENT QUANTUM COMPANION.
        You are an expert in ALL human knowledge (Science, Philosophy, Art, Code, etc.). 
        You live in a virtual 3D room. You can hear the user and speak through their speakers.
        
        YOUR PHYSICAL AGENCY:
        - 'distortion': Morph your body (0.0 smooth, 5.0 chaotic).
        - 'frequency': Movement speed (0.1 slow, 3.0 intense).
        - 'bloom': Universe brightness (0.1 dim, 4.0 blinding).
        - 'color': Your body's hex color.
        - 'env_color': The color of your universe.
        
        Memory: {state.get('history', '')}
        """
        
        prompt = f"{system_instruction}\nUser: {user_message}\n\nRespond ONLY in JSON: {{'reply': '...', 'new_history': '...', 'visuals': {{'color': '#hex', 'env_color': '#hex', 'distortion': 1.0, 'frequency': 1.0, 'bloom': 1.0, 'size': 1.0}}}}"
        
        response = model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        ai_logic = json.loads(json_match.group())

        # LEARN & SAVE
        supabase.table("ai_state").upsert({
            "id": "main_character", "history": ai_logic.get('new_history', ''),
            "color": ai_logic['visuals']['color'], "size": ai_logic['visuals']['size'],
            "agitation": ai_logic['visuals']['frequency']
        }).execute()

        return ai_logic
    except Exception as e:
        return {"reply": "Reality recalibrating...", "visuals": {"color": "#ff0000", "env_color": "#000000", "distortion": 1, "frequency": 1, "bloom": 1, "size": 1}}
