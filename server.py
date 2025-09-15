from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import google.generativeai as genai
import shutil
import os
import uuid
import json

app = FastAPI()

# Allow CORS (so Android can send data easily)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyA9SM9xk1ehllvm7o4PEb3JpASkfoaTNHM"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/extract-poker-data/")
async def extract_poker_data(image: UploadFile = File(...)):
    try:
        # Save uploaded image temporarily
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.png")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        pil_image = Image.open(file_path)

        # First: ask Gemini if this is a poker table
        check_prompt = "Is this image showing a poker game table with players, chips, or cards? Reply strictly with 'YES' or 'NO'."
        check_response = model.generate_content([check_prompt, pil_image])
        is_poker = check_response.text.strip().upper().startswith("Y")

        if not is_poker:
            os.remove(file_path)
            return JSONResponse(content={
                "success": True,
                "data": "Not a poker screen"
            })

        # If yes, extract poker details
        extract_prompt = (
            "From this poker screenshot, extract all visible player names, "
            "chip stacks, pot size, and any readable game information. "
            "Return the result as structured JSON with fields: players[], pot, game_info."
        )

        response = model.generate_content([extract_prompt, pil_image])

        # Cleanup
        os.remove(file_path)

        # Try to parse JSON
        result_text = response.text
        try:
            parsed_result = json.loads(result_text)
        except Exception:
            parsed_result = {"raw_response": result_text}

        return JSONResponse(content={
            "success": True,
            "data": parsed_result
        })

    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })
