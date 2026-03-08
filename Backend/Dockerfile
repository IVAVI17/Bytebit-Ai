FROM python:3.11-slim

# Install system dependencies for pyodbc (MSSQL) and OpenCV
RUN apt-get update && apt-get install -y \
    unixodbc-dev unixodbc libpq-dev g++ curl gnupg2 \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft ODBC Driver 17 for SQL Server 
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,armhf,arm64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Start the uvicorn server
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
