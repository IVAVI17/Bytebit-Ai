import uvicorn
import pickle
import pathlib
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from database import  SessionLocal
from sqlalchemy.orm import Session
from create_table import Login
from create_table import Patient
from create_table import Doctor
from fastapi.middleware.cors import CORSMiddleware
import datetime
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import timedelta
from fastapi.responses import JSONResponse
import speech_recognition as sr
from pydub import AudioSegment
import speech_recognition as sr
from fastapi import File, UploadFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi.responses import FileResponse
import os
from PIL import Image
import assemblyai as aai
import google.generativeai as genai
import json
from dotenv import load_dotenv

# Load keys from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Assembly AI Key
ASSEMBLY_AI_KEY = os.getenv("ASSEMBLY_AI_KEY", "your_assembly_ai_key_here")

# Initialize Gemini Model
model = genai.GenerativeModel('gemini-2.5-flash')

async def extract_entities_with_llm(transcript_text: str, schema_type: str):
    """
    Uses Gemini to extract structured medical data from transcripts.
    """
    if schema_type == "new_patient":
        prompt = f"""
        Extract patient details from the following transcript into a JSON object.
        Transcript: "{transcript_text}"
        
        Required JSON Keys:
        - "NAME OF PATIENT" (String)
        - "AGE" (Number/Integer)
        - "WEIGHT" (String, e.g., "70 kg")
        - "NUMBER" (String, contact no)
        - "ADDRESS" (String)
        - "DATE OF ADMISSION" (String, YYYY-MM-DD)
        
        Return ONLY the JSON object. If a value is missing, use null.
        """
    else: # doctor_conversation
        prompt = f"""
        Extract clinical details from this doctor-patient conversation transcript into a JSON object.
        Transcript: "{transcript_text}"
        
        Required JSON Keys:
        - "SYMPTOMS" (String, comma separated if multiple)
        - "DISEASE" (String)
        - "MEDICINE" (String, comma separated)
        - "DIAGNOSIS" (String)
        
        Return ONLY the JSON object. If a value is missing, use null.
        """
    
    response = model.generate_content(prompt)
    try:
        # Clean response text in case LLM adds markdown backticks
        json_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return {}

# Temporarily change PosixPath to WindowsPath
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# OAuth2PasswordBearer object to handle token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Authenticate user
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Login).filter(Login.username == username, Login.password == password).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

#C:\Users\Kartikey\Desktop\MedTalk Ai\Backend\app.py
# Create JWT token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Login).filter(Login.username == username).first()
    if user is None:
        raise credentials_exception
    return user

class Token(BaseModel):
    access_token: str
    token_type: str
    hospital_id: int
# Login endpoint to generate JWT token

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_db = db.query(Login).filter(Login.username == form_data.username).first()
    hospital_id = user_db.hospital_id
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "hospital_id": hospital_id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer", hospital_id=hospital_id)

def check_hospital_access(current_user: Login = Depends(get_current_user), hospital_id: int = None):
    if current_user.hospital_id != hospital_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

def check_patient_access(current_user: Login = Depends(get_current_user), hospital_id: int = None, patient_id: int = None):
    if current_user.hospital_id != hospital_id or current_user.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

# Revert the changes back to the original value
pathlib.PosixPath = temp

@app.get('/')
def index():
    return {'message': 'Hello, World'}


# @app.post('/login')
# def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
#     # Check if the username and password match the data in the database
#     user = db.query(Login).filter(Login.username == username, Login.password == password).first()
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid username or password")
    
#     # Return success along with the hospital ID
#     return {"message": "Login successful", "hospital_id": user.hospital_id}

@app.get("/fetch_hospital_name")
async def get_hospital_name(hospital_id: int, db: Session = Depends(get_db)):
    login = db.query(Login).filter(Login.hospital_id == hospital_id).first()
    if not login:
        return {"error": "Hospital not found"}
    return {"hospital_name": login.hospital_name}

# Route to predict entities
# @app.post('/newpatient')
# def predict_entities(text: str):
#     # Process the text using the NER model
#     doc = nlp_ner(text)
    
#     # Extract mapped entities
#     mapped = []
#     for ent in doc.ents:
#         mapped.append({
#             "value": ent.text,
#             "label": ent.label_
#         })
    
#     return mapped

def get_session_local():
    return SessionLocal()

@app.post('/newpatient')
async def add_new_patient(
    hospital_id: int,
    audio_file: UploadFile = File(...),
    current_user: Login = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_hospital_access(current_user, hospital_id)
    
    audio_content = await audio_file.read()
    temp_path = "temp_patient.mp3"
    with open(temp_path, "wb") as f:
        f.write(audio_content)
    
    aai.settings.api_key = ASSEMBLY_AI_KEY
    transcriber = aai.Transcriber()
    
    config = aai.TranscriptionConfig(speech_models=["universal-3-pro", "universal-2"], language_detection=True)
    transcript = transcriber.transcribe(temp_path, config=config)
    if transcript.error:
         return JSONResponse(status_code=500, content={"error": f"AssemblyAI transcription failed: {transcript.error}"})
    
    # Process the text using Gemini LLM
    patient_data = await extract_entities_with_llm(transcript.text, "new_patient")
    
    # Initialize a new Patient object
    doa = datetime.datetime.now().strftime("%Y-%m-%d") if not patient_data.get("DATE OF ADMISSION") else patient_data["DATE OF ADMISSION"]
    age = patient_data.get("AGE")
    try:
        age = int(age) if age is not None else None
    except ValueError:
        age = None
    new_patient = Patient(
        name=patient_data.get("NAME OF PATIENT", None),
        age=age,
        weight=patient_data.get("WEIGHT", None),
        contact_no=patient_data.get("NUMBER", None),
        address=patient_data.get("ADDRESS", None),
        doa=doa,
        hospital_id=hospital_id
    )
    
    # Save the new patient to the database
    try:
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        return {"message": "Patient added successfully", "patient_id": new_patient.patient_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add patient: {str(e)}")
    
    
@app.get("/patients/{hospital_id}")
async def get_patients(
    hospital_id: int, 
    current_user: Login = Depends(get_current_user),
    db: Session = Depends(get_db)):
    check_hospital_access(current_user, hospital_id)
    patients = db.query(Patient).filter(Patient.hospital_id == hospital_id).all()
    if not patients:
        return {"patients": []}
    
    # Extract patient names and dates of admission
    patient_data = [{"name": patient.name, "doa": patient.doa, "id":patient.patient_id} for patient in patients]
    
    return {"patients": patient_data}

@app.post('/doctorconversation')
async def doctor_conversation(
    patient_id: int,
    hospital_id: int,
    audio_file: UploadFile = File(...),
    current_user: Login = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #check_patient_access(current_user, hospital_id, patient_id)
    check_hospital_access(current_user, hospital_id)

    audio_content = await audio_file.read()
    temp_path = "temp_doc.mp3"
    with open(temp_path, "wb") as f:
        f.write(audio_content)
    
    # Perform speech recognition with AssemblyAI (replaced Google SR for accuracy)
    aai.settings.api_key = ASSEMBLY_AI_KEY
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(speech_models=["universal-3-pro", "universal-2"], language_detection=True)
    transcript = transcriber.transcribe(temp_path, config=config)

    if transcript.error:
         return JSONResponse(status_code=500, content={"error": f"AssemblyAI transcription failed: {transcript.error}"})
    
    # Process the text using Gemini LLM
    entities = await extract_entities_with_llm(transcript.text, "doctor_conversation")
    
    # Initialize a new Doctor object
    new_record = Doctor(
        symptoms=entities.get("SYMPTOMS", None),
        disease=entities.get("DISEASE", None),
        medicine=entities.get("MEDICINE", None),
        diagnosis=entities.get("DIAGNOSIS", None),
        med_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        hospital_id=hospital_id,
        patient_id=patient_id
    )
    
    # Save the new record to the database
    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return {"message": "Doctor's conversation recorded successfully", "record_id": new_record.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record doctor's conversation: {str(e)}")
    
# @app.get("/doctors/{hospital_id}/{patient_id}")
# def get_doctors(patient_id: int, hospital_id: int, db: Session = Depends(get_db)):
#     doctors = db.query(Doctor).filter(Doctor.patient_id == patient_id, Doctor.hospital_id == hospital_id).all()
#     if not doctors:
#         return {"message": "No doctors found for this patient in the specified hospital"}
    
#     # Extract doctor details
#     doctor_data = []
#     for doctor in doctors:
#         doctor_data.append({
#             "id": doctor.id,
#             "symptoms": doctor.symptoms,
#             "disease": doctor.disease,
#             "medicine": doctor.medicine,
#             "diagnosis": doctor.diagnosis,
#             "med_time": doctor.med_time
#         })
    
#     return {"doctors": doctor_data}

@app.get("/patients_and_doctors/{hospital_id}/{patient_id}")
async def get_patients_and_doctors(
    patient_id: int, 
    hospital_id: int,
    current_user: Login = Depends(get_current_user),
    db: Session = Depends(get_db)):
    # Fetch patient details
    check_hospital_access(current_user, hospital_id)
    patient = db.query(Patient).filter(Patient.patient_id == patient_id, Patient.hospital_id == hospital_id).first()
    if not patient:
        return {"message": "No patient found for this ID and hospital"}
    
    patient_data = {
        "patient_id": patient.patient_id,
        "name": patient.name,
        "age": patient.age,
        "weight": patient.weight,
        "contact_no": patient.contact_no,
        "address": patient.address,
        "doa": patient.doa
    }

    # Fetch doctor details
    doctors = db.query(Doctor).filter(Doctor.patient_id == patient_id, Doctor.hospital_id == hospital_id).all()
    if not doctors:
        return {"patient": patient_data, "doctors": []}  # Return empty list for doctors if not found
    
    doctor_data = []
    for doctor in doctors:
        doctor_data.append({
            "id": doctor.id,
            "symptoms": doctor.symptoms,
            "disease": doctor.disease,
            "medicine": doctor.medicine,
            "diagnosis": doctor.diagnosis,
            "med_time": doctor.med_time
        })
    
    return {"patient": patient_data, "doctors": doctor_data}
@app.get("/generate_pdf/{hospital_id}/{patient_id}")
async def generate_pdf(
    patient_id: int, 
    hospital_id: int,
    current_user: Login = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch patient details
    check_hospital_access(current_user, hospital_id)
    patient = db.query(Patient).filter(Patient.patient_id == patient_id, Patient.hospital_id == hospital_id).first()
    if not patient:
        return {"message": "No patient found for this ID and hospital"}
    
    patient_data = {
        "Patient ID": patient.patient_id,
        "Name": patient.name,
        "Age": patient.age,
        "Weight": patient.weight,
        "Contact No": patient.contact_no,
        "Address": patient.address,
        "Date of Admission": patient.doa
    }

    # Fetch doctor details
    doctors = db.query(Doctor).filter(Doctor.patient_id == patient_id, Doctor.hospital_id == hospital_id).all()
    doctor_data = []
    for doctor in doctors:
        doctor_data.append({
            "ID": doctor.id,
            "Symptoms": doctor.symptoms,
            "Disease": doctor.disease,
            "Medicine": doctor.medicine,
            "Diagnosis": doctor.diagnosis,
            "Medication Time": doctor.med_time
        })

    # Generate PDF
    pdf_filename = f"patient_{patient_id}_report.pdf"
    pdf_path = f"C:/Users/Kartikey/Desktop/test/{pdf_filename}"  # Update the path where you want to save the PDF
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    y = 750
    for key, value in patient_data.items():
        if value:  # Exclude empty or null fields
            c.drawString(100, y, f"{key}: {value}")
            y -= 20
    
    y -= 20
    c.drawString(100, y, "Doctor's Details:")
    y -= 20
    for doctor in doctor_data:
        for key, value in doctor.items():
            if value:  # Exclude empty or null fields
                c.drawString(120, y, f"{key}: {value}")
                y -= 20
    c.save()

    # Download PDF
    return FileResponse(pdf_path, filename=pdf_filename)

@app.post("/prescription_ocr")
async def prescription_ocr(
    hospital_id: int,
    image_file: UploadFile = File(...),
    current_user: Login = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_hospital_access(current_user, hospital_id)
    
    # Read the image content
    image_content = await image_file.read()
    temp_image_path = "temp_prescription.jpg"
    with open(temp_image_path, "wb") as f:
        f.write(image_content)
        
    # Open image with PIL
    try:
        img = Image.open(temp_image_path)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid image file: {str(e)}"})

    prompt = """
    Extract details from this medical prescription image into a JSON object.
    
    Required JSON Keys:
    - "PATIENT_NAME" (String)
    - "DOCTOR_NAME" (String)
    - "DATE" (String, YYYY-MM-DD format if possible)
    - "MEDICINES" (List of Objects, each having "NAME", "DOSAGE", "FREQUENCY", "DURATION")
    
    Return ONLY the JSON object. If a value is missing or unreadable, use null.
    """
    
    try:
        response = model.generate_content([prompt, img])
        json_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_text)
        return {"message": "Success", "extracted_data": data}
    except Exception as e:
        print(f"Error parsing LLM response or image: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to extract prescription data from image", "details": str(e)})

@app.post("/logout")
async def logout():
    return {"message": "User logged out successfully"}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
# uvicorn app:app --reload
# docker build -t models .
# Run the Docker container
# docker run -d -p 8000:8000 models
# uvicorn app:app --reload --host 127.0.0.1 --port 8000






