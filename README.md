# 🏥 Healthcare Workflow Automation System

> **Transforming Healthcare Delivery in India Through AI-Powered Paperless Workflows**

[![AI for Bharat Hackathon](https://img.shields.io/badge/AI%20for%20Bharat-Hackathon%202025-blue)](https://aiforbharat.com)
[![Built with Kiro](https://img.shields.io/badge/Built%20with-Kiro-purple)](https://kiro.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Problem Statement

In India's healthcare system, **paper-based workflows create critical inefficiencies**:
- ⏰ Hours wasted on manual data entry
- 📝 Errors from illegible handwriting
- 📄 Lost or misplaced patient forms
- 🔍 Inaccessible patient history during consultations
- 🗣️ Language barriers for non-English speaking patients

**Our solution**: A comprehensive AI-powered system that digitizes the entire hospitalization process, from appointment booking to prescription delivery, making healthcare more efficient, accurate, and accessible.

---

## 💡 Solution Overview

### **End-to-End Paperless Healthcare Workflow**

```
Patient WhatsApp → AI Booking → Pre-Consultation Updates → Digital Prescription → Medicine Reminders → Analytics Dashboard
```

Our system eliminates paper at every touchpoint while leveraging AI to handle the complexity of multilingual communication, handwriting recognition, and intelligent data extraction.

---

## ✨ Key Features

### 1. 📱 **WhatsApp-Based Appointment Booking**
- **Multilingual Support**: English, Hindi, Tamil, Telugu, Bengali, Marathi
- **Conversational Interface**: Natural language booking flow
- **Smart Scheduling**: Symptom-based doctor matching
- **Automated Reminders**: 24-hour and 1-hour appointment notifications

**Why AI?** Natural language understanding across multiple languages and dialects requires sophisticated NLP models that can handle conversational variations and extract structured information from unstructured patient inputs.

### 2. 🎤 **Pre-Consultation Patient Updates**
- **Text & Audio Support**: Patients can send health updates via text or voice messages
- **Automatic Transcription**: AI converts audio to text in any supported language
- **Medical Entity Extraction**: AI identifies symptoms, conditions, and relevant medical information
- **Structured Storage**: Updates are tagged and stored for doctor review

**Why AI?** Speech recognition with medical terminology, accent handling, and entity extraction from unstructured patient narratives cannot be achieved with rule-based systems.

### 3. ✍️ **Digital Prescription System**
- **iPad Handwriting Capture**: Doctors write naturally on tablets
- **OCR Extraction**: AI reads handwritten prescriptions with high accuracy
- **Structured Data**: Automatically extracts medicines, dosages, diagnosis, and notes
- **PDF Generation**: Creates professional prescription documents
- **WhatsApp Delivery**: Sends prescriptions directly to patients

**Why AI?** Doctor handwriting varies significantly and includes medical abbreviations. Deep learning OCR models trained on medical handwriting are essential for accurate extraction.

### 4. 💊 **Post-Consultation Engagement**
- **Review Collection**: Automated feedback requests
- **Medicine Reminders**: Smart scheduling based on prescription frequency
- **Adherence Support**: Reminders throughout medication course

### 5. 🤖 **AI-Powered Doctor Dashboard**
- **Conversational Queries**: "When did patient XYZ last visit?"
- **Patient History**: Complete medical history at your fingertips
- **Hospital Analytics**: Patient volume, doctor performance, treatment patterns
- **Graph Database**: Semantic search for similar cases and patterns

**Why AI?** LLMs enable natural language to database query translation, allowing doctors to access information conversationally without learning complex query syntax. Graph databases with AI enable semantic understanding of medical relationships.

---

## 🏗️ Architecture

### **Microservices-Based Design**

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  WhatsApp Client │         │ Doctor Dashboard │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway Layer                          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 Application Services                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │WhatsApp  │  │Appointment│  │Prescription│ │Analytics │   │
│  │Bot Service│  │ Service  │  │  Service  │  │ Service  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    AI/ML Services                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   OCR    │  │   NLP    │  │Transcription│ │   LLM   │   │
│  │ Service  │  │Extraction│  │  Service  │  │  Query  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │PostgreSQL│  │  Neo4j   │  │  Redis   │                  │
│  │   (SQL)  │  │ (Graph)  │  │ (Cache)  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### **Technology Stack**

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI |
| **Databases** | PostgreSQL (transactional), Neo4j (graph), Redis (cache) |
| **AI/ML** | TrOCR/PaddleOCR, spaCy NER, OpenAI Whisper, LangChain + GPT-4 |
| **Integration** | WhatsApp Business API (Meta) |
| **Frontend** | React 18+ with TypeScript, Material-UI |
| **Infrastructure** | Docker, Kubernetes/ECS |
| **Storage** | AWS S3 / MinIO |

---

## 🎨 User Journey

### **Patient Experience**

```mermaid
graph LR
    A[Send 'Hi' to<br/>WhatsApp] --> B[Select<br/>Language]
    B --> C[Provide<br/>Details]
    C --> D[Choose<br/>Doctor Slot]
    D --> E[Get<br/>Confirmation]
    E --> F[Send Health<br/>Updates]
    F --> G[Attend<br/>Consultation]
    G --> H[Receive<br/>Prescription]
    H --> I[Get Medicine<br/>Reminders]
```

### **Doctor Experience**

```mermaid
graph LR
    A[View Patient<br/>Updates] --> B[Conduct<br/>Consultation]
    B --> C[Write<br/>Prescription]
    C --> D[AI Extracts<br/>Data]
    D --> E[Verify &<br/>Confirm]
    E --> F[Query Patient<br/>History]
    F --> G[View<br/>Analytics]
```

---

## 🚀 Getting Started

### **Prerequisites**

- Python 3.11+
- Docker & Docker Compose
- WhatsApp Business API credentials
- OpenAI API key (for LLM features)

### **Installation**

```bash
# Clone the repository
git clone https://github.com/yourusername/healthcare-workflow-automation.git
cd healthcare-workflow-automation

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Start infrastructure services
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start the application
uvicorn main:app --reload
```

### **Configuration**

Create a `.env` file with the following:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/healthcare_db
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379

# WhatsApp Business API
WHATSAPP_API_TOKEN=your_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_id

# AI Services
OPENAI_API_KEY=your_openai_key
OCR_SERVICE_URL=http://localhost:8001

# Security
JWT_SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key
```

---

## 📊 Why AI is Essential

This system demonstrates **meaningful AI usage** in healthcare automation:

### 1. **Handwriting Recognition (OCR)**
Traditional OCR fails with doctor handwriting. We use **deep learning models** trained on medical handwriting datasets to achieve high accuracy with variable handwriting styles and medical abbreviations.

### 2. **Natural Language Understanding (NLP)**
Patients describe symptoms in conversational language across multiple languages. **AI-powered NLP** extracts structured medical entities (symptoms, conditions, medications) from unstructured text—impossible with rule-based systems.

### 3. **Speech Recognition & Transcription**
Converting multilingual audio with medical terminology, Indian accents, and background noise requires **sophisticated speech recognition models** like OpenAI Whisper.

### 4. **Conversational Database Queries**
**LLMs enable semantic understanding** of natural language queries and translate them to database queries. Doctors can ask "When did patient XYZ last visit?" instead of writing SQL.

### 5. **Graph-Based Semantic Search**
**Graph databases + LLMs** enable queries like "find patients with similar symptoms" that go beyond keyword matching, understanding medical relationships and patterns.

---

## 🔒 Privacy & Security

- ✅ **End-to-end encryption** for all patient data
- ✅ **TLS 1.3** for data in transit
- ✅ **Role-based access control** (RBAC)
- ✅ **Audit logging** for all data access
- ✅ **Synthetic data** for testing and demos
- ✅ **GDPR-compliant** data deletion
- ✅ **No third-party AI data sharing** (self-hosted models preferred)

---

## ⚠️ Limitations & Responsible Use

This system is designed to **support healthcare professionals**, not replace clinical judgment:

1. **AI Accuracy**: OCR and extraction models may make errors. Doctors must review all AI-extracted information.
2. **Medical Advice**: The WhatsApp bot does not provide medical advice or diagnosis—it's a scheduling tool only.
3. **Emergency Care**: Not suitable for emergencies. Patients should contact emergency services directly.
4. **Data Quality**: AI insights depend on data quality. Incomplete data affects analytics.
5. **Language Accuracy**: Multilingual support accuracy varies by language and training data.
6. **Connectivity Required**: No offline functionality.

---

## 📁 Repository Structure

```
healthcare-workflow-automation/
├── requirements.md          # Detailed requirements specification
├── design.md               # System architecture and design
├── tasks.md                # Implementation plan
├── README.md               # This file
├── src/
│   ├── services/           # Microservices
│   │   ├── whatsapp_bot/
│   │   ├── appointment/
│   │   ├── prescription/
│   │   ├── analytics/
│   │   └── reminder/
│   ├── ai_services/        # AI/ML services
│   │   ├── ocr/
│   │   ├── nlp/
│   │   ├── transcription/
│   │   └── llm_query/
│   ├── models/             # Data models
│   ├── repositories/       # Data access layer
│   └── utils/              # Utilities
├── tests/                  # Test suite
├── docker-compose.yml      # Local development setup
└── requirements.txt        # Python dependencies
```

---

## 🧪 Testing

We use **property-based testing** with Hypothesis to ensure correctness:

```bash
# Run all tests
pytest

# Run property-based tests
pytest tests/property_tests/

# Run integration tests
pytest tests/integration/

# Generate test coverage report
pytest --cov=src --cov-report=html
```

---

## 🎯 Hackathon Submission

**AI for Bharat Hackathon - Professional Track**

**Category**: AI for Healthcare & Life Sciences

**Focus**: Workflow automation for healthcare professionals

This project was developed using **Kiro**, an AI-assisted development tool, following spec-driven development methodology.

### **Submission Checklist**
- ✅ requirements.md - Comprehensive requirements specification
- ✅ design.md - System architecture and design document
- ✅ README.md - Project overview and documentation
- ✅ Synthetic data only - No real patient information
- ✅ Clear AI justification - Explains why AI is needed
- ✅ Responsible design - Limitations clearly stated

---

## 🤝 Contributing

This is a hackathon project, but contributions are welcome! Please read our contributing guidelines and code of conduct.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

Developed for the AI for Bharat Hackathon 2025

---

## 🙏 Acknowledgments

- **Kiro** - AI-assisted development platform
- **AI for Bharat** - Hackathon organizers
- **WhatsApp Business API** - Communication platform
- **OpenAI** - LLM and transcription services
- **Open source community** - Various libraries and tools

---

## 📞 Contact

For questions or feedback, please open an issue or reach out to the team.

---

<div align="center">

**Built with ❤️ for better healthcare in India**

[View Requirements](requirements.md) | [View Design](design.md) | [View Tasks](tasks.md)

</div>
