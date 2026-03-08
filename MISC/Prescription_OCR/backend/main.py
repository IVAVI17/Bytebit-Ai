
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from ocr_pipeline import process_image
from typing import Optional

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(default=""),
    image_name: Optional[str] = Form(default="")
):
    contents = await file.read()

    result = process_image(contents, patient_id=patient_id, image_name=(image_name or file.filename))

    return result