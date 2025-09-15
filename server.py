from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import google.generativeai as genai
import shutil
import os
import uuid

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

        # Open image and send to Gemini
        pil_image = Image.open(file_path)
        prompt = (
            "From this poker screenshot, extract all visible player names, "
            "chip stacks, and any readable game information. "
            "Return the result as structured JSON."
        )

        response = model.generate_content([prompt, pil_image])

        # Cleanup uploaded file
        os.remove(file_path)

        # Attempt to parse JSON from the response
        result_text = response.text
        try:
            import json
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
