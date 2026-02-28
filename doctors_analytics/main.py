from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq

from db import run_read_query
from faiss_index import build_index, semantic_search


# ------------------------
# Groq Setup
# ------------------------

GROQ_API_KEY = "YOUR_GROQ_KEY"

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "openai/gpt-oss-120b"


# ------------------------
# FastAPI
# ------------------------

app = FastAPI()


class Query(BaseModel):
    question: str


SCHEMA = """
Table name: master

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


# ------------------------
# SQL Generation
# ------------------------

def generate_sql(question):

    prompt = f"""
You are a hospital data assistant.

Use ONLY the schema below.

Generate SQL SELECT query.

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


# ------------------------
# Query Router
# ------------------------

def route_query(question):

    question_lower = question.lower()

    if "note" in question_lower or "symptom" in question_lower:
        return "semantic"

    if "trend" in question_lower or "dashboard" in question_lower:
        return "dashboard"

    return "sql"


# ------------------------
# Dashboard Insights
# ------------------------

def dashboard_insights():

    disease = run_read_query("""
    SELECT diagnosis, COUNT(*) AS total
    FROM master
    GROUP BY diagnosis
    ORDER BY total DESC
    """)

    doctor_load = run_read_query("""
    SELECT doctor_name, COUNT(*) AS patients
    FROM master
    GROUP BY doctor_name
    ORDER BY patients DESC
    """)

    gender_dist = run_read_query("""
    SELECT gender, COUNT(*) AS total
    FROM master
    GROUP BY gender
    """)

    return {
        "disease_distribution": disease,
        "doctor_workload": doctor_load,
        "gender_distribution": gender_dist
    }


# ------------------------
# Ask Endpoint
# ------------------------

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

    # default SQL route
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
