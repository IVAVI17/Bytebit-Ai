from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from db import run_read_query, add_record
from faiss_index import build_index, semantic_search

# ... (existing Groq setup code remains the same)

GROQ_API_KEY = "your_groq_api_key_here"  # Replace with your actual Groq API key
client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "openai/gpt-oss-120b"

app = FastAPI()

class Query(BaseModel):
    question: str

SCHEMA = """
Table name: analytics (Google Sheets)

Columns:
patient_id
patient_name
age
gender
doctor_id
doctor_name
diagnosis
visit_date
medication
medication_duration
symptoms
cure
patient_notes
doctor_notes
"""

def generate_sql(question):
    """Generate SQL for Google Sheets queries"""
    prompt = f"""
You are a hospital data assistant.

Use ONLY the schema below to generate SQL SELECT queries.
The data is stored in Google Sheets, so use simple SQL syntax.

Schema:
{SCHEMA}

Return only SQL.

Question:
{question}
"""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def route_query(question):
    question_lower = question.lower()
    
    if "note" in question_lower or "symptom" in question_lower:
        return "semantic"
    
    if "trend" in question_lower or "dashboard" in question_lower:
        return "dashboard"
    
    return "sql"

def dashboard_insights():
    """Get analytics from Google Sheets"""
    
    # Disease distribution
    disease = run_read_query("""
    SELECT diagnosis, COUNT(*) AS total
    FROM analytics
    GROUP BY diagnosis
    """)
    
    # Doctor workload
    doctor_load = run_read_query("""
    SELECT doctor_name, COUNT(*) AS patients
    FROM analytics
    GROUP BY doctor_name
    """)
    
    # Gender distribution
    gender_dist = run_read_query("""
    SELECT gender, COUNT(*) AS total
    FROM analytics
    GROUP BY gender
    """)
    
    return {
        "disease_distribution": disease,
        "doctor_workload": doctor_load,
        "gender_distribution": gender_dist
    }

@app.post("/ask")
def ask(data: Query):
    question = data.question
    route = route_query(question)
    
    if route == "semantic":
        results = semantic_search(question)
        return {
            "type": "semantic",
            "results": results
        }
    
    if route == "dashboard":
        insights = dashboard_insights()
        return {
            "type": "dashboard",
            "data": insights
        }
    
    # SQL route
    sql = generate_sql(question)
    rows = run_read_query(sql)
    
    return {
        "type": "sql",
        "sql": sql,
        "data": rows
    }

@app.get("/")
def home():
    return {"message": "Hospital AI System Running"}

@app.on_event("startup")
def startup():
    build_index()