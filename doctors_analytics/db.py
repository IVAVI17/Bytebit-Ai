import mysql.connector


def get_main_db_connection():
    """Connect to MySQL database"""

    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="purpledocs",
        password="purplebits1",
        database="hospital_patient_project"
    )

    return conn


def run_read_query(query: str):

    # Safety: allow only SELECT queries
    if not query.lower().strip().startswith("select"):
        raise Exception("Only SELECT queries are allowed")

    conn = get_main_db_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(query)

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result