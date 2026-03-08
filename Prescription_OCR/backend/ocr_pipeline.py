
import os
import io
import base64
import datetime
import gspread
import requests
import json
from PIL import Image
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS

# ========= GOOGLE SHEETS CONFIG =========
SPREADSHEET_ID = "1LWhTGN3mNYqe7gtuRNAKBx8W87HtO5QmLPxv-8zWCc8"
SHEET_OCR_RESULTS = "OCR_Results"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    GOOGLE_CREDENTIALS, scopes=SCOPES
)
client = gspread.authorize(creds)
ss = client.open_by_key(SPREADSHEET_ID)

def get_sheet(name):
    return ss.worksheet(name)

def init_ocr_sheet():
    """Create OCR_Results sheet if it doesn't exist"""
    try:
        ss.worksheet(SHEET_OCR_RESULTS)
    except:
        ss.add_worksheet(SHEET_OCR_RESULTS, rows="1000", cols="10")
        sh = get_sheet(SHEET_OCR_RESULTS)
        sh.append_row([
            "Timestamp",
            "Patient_ID",
            "Extracted_Text",
            "Medication",
            "Dosage",
            "Duration",
            "Side_Effects",
            "Image_Name",
            "Status",
            "Notes"
        ])

def save_ocr_result(extracted_text, patient_id="", image_name="", additional_data=None):
    """Save OCR extracted text to Google Sheets"""
    init_ocr_sheet()
    
    sheet = get_sheet(SHEET_OCR_RESULTS)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Parse extracted text to extract key fields (you can enhance this)
    medication = extracted_text.split('\n')[0] if extracted_text else ""
    
    row = [
        timestamp,
        patient_id,
        extracted_text,
        medication,  # You can enhance parsing
        "",  # Dosage - to be filled
        "",  # Duration - to be filled
        "",  # Side effects - to be filled
        image_name,
        "Pending_Review",
        ""
    ]
    
    sheet.append_row(row)
    print(f"✓ OCR result saved to Google Sheets")



def process_image(image_bytes, patient_id="", image_name=""):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    # Add a white background
    white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white_bg.paste(image, (0, 0), image)
    rgb_image = white_bg.convert("RGB")
    # Save the image being sent to the LLM for inspection
    rgb_image.save("sent_to_llm.png")
    buffered = io.BytesIO()
    rgb_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    prompt = (
        "Extract and return only the exact text that appears in the image. "
        "Do not add, interpret, or format anything. Output only the raw recognized text, exactly as it is written in the image, in the LLM output I dont want any extra things or text just what is mentioned in the text"
    )

    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    payload = {
        "model": "accounts/fireworks/models/kimi-k2p5",
        "max_tokens": 4096,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.6,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}]}
        ]
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('FIREWORKS_API_KEY', 'fw_WUbj2iSi6bqasaKG92Et8n')}"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    try:
        result = response.json()
        llm_output = result["choices"][0]["message"]["content"]
    except Exception:
        llm_output = response.text
    print("LLM Output:\n", llm_output)
    save_ocr_result(
        extracted_text=llm_output,
        patient_id=patient_id,
        image_name=image_name
    )
    
    return {
        "llm_output": llm_output,
        "saved_to_sheets": True
    }