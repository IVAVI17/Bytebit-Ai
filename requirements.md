# Requirements Document: Healthcare Workflow Automation System

## Introduction

This document specifies requirements for a healthcare workflow automation system designed to digitize and streamline the hospitalization process in India. The system eliminates paper-based workflows through WhatsApp-based patient interaction, AI-powered data extraction, digital prescriptions, and intelligent analytics dashboards for healthcare professionals.

The system addresses critical inefficiencies in healthcare delivery: time wasted on manual data entry, errors from illegible handwriting, lost paper forms, and lack of accessible patient history. By leveraging AI for natural language processing, handwriting recognition, and intelligent querying, the system provides meaningful automation that adapts to multilingual inputs, extracts medical information from unstructured data, and enables conversational access to patient records.

## Glossary

- **Patient_Update**: Text or audio message sent by Patient between booking and consultation
- **Master_Database**: Relational database storing all the details related to the patient
- **Graph_Database**: Graph-structured database enabling semantic queries via LLM
- **Transcription_Service**: AI service converting audio messages to text
- **OCR_Service**: Optical Character Recognition service extracting text from handwritten prescriptions
- **Reminder_Service**: Automated service sending scheduled notifications via WhatsApp
- **Review_Request**: Post-consultation request for Patient feedback on Doctor and hospital

## Requirements

### Requirement 1: WhatsApp-Based Appointment Booking

**User Story:** As a Patient, I want to book appointments through WhatsApp in my preferred language, so that I can schedule consultations without visiting the hospital or using complex apps.

#### Acceptance Criteria

1. WHEN a Patient sends "hi" to the hospital WhatsApp number, THE WhatsApp_Bot SHALL respond with a greeting and language selection options
2. WHEN a Patient selects a language, THE WhatsApp_Bot SHALL conduct all subsequent interactions in that language
3. WHEN the WhatsApp_Bot requests patient information, THE System SHALL collect name, age, sex, and symptoms through conversational prompts
4. WHEN a Patient selects a time slot, THE System SHALL create an Appointment record and confirm the booking
5. WHEN an Appointment is created, THE System SHALL store all collected information in the Master_Database
6. WHEN an Appointment is 24 hours away, THE Reminder_Service SHALL send a reminder message to the Patient via WhatsApp
8. WHEN an Appointment is 1 hour away, THE Reminder_Service SHALL send a final reminder message to the Patient via WhatsApp

### Requirement 2: Pre-Consultation Patient Updates

**User Story:** As a Patient, I want to send health updates between booking and my appointment, so that my Doctor has current information before the consultation.

#### Acceptance Criteria

1. WHEN a Patient with an active Appointment sends a text message, THE System SHALL store it as a Patient_Update in the Master_Database
2. WHEN a Patient with an active Appointment sends an audio message, THE Transcription_Service SHALL convert it to text
3. WHEN audio transcription completes, THE System SHALL store the transcribed text as a Patient_Update
4. WHEN a Patient_Update is stored, THE AI_Extractor SHALL analyze the content and extract medical information
5. WHEN medical information is extracted, THE System SHALL tag the Patient_Update with extracted entities and store them in structured format
6. WHEN a Patient sends updates in any supported language, THE System SHALL process them correctly

### Requirement 3: Handwritten Prescription Digitization

**User Story:** As a Doctor, I want to write prescriptions naturally on an iPad and have them automatically digitized, so that I can maintain my workflow while eliminating paper and improving accuracy.

#### Acceptance Criteria

1. WHEN a Doctor writes on the Dashboard iPad interface, THE System SHALL capture the handwritten prescription as an image
2. WHEN a prescription image is captured, THE OCR_Service SHALL extract text from the handwriting
3. WHEN text is extracted, THE AI_Extractor SHALL identify and structure: medicines, dosage, course duration, diagnosis, and medical notes
4. WHEN extraction fails or confidence is low, THE System SHALL prompt the Doctor to verify or correct the extracted information
5. WHEN structured prescription data is confirmed, THE System SHALL store it in the Master_Database linked to the Patient and Appointment
6. WHEN prescription data is stored, THE System SHALL generate a formatted PDF prescription document
7. WHEN PDF generation completes, THE System SHALL send the prescription PDF to the Patient via WhatsApp

### Requirement 4: Post-Consultation Engagement

**User Story:** As a hospital administrator, I want to collect patient feedback and support medication adherence, so that we can improve service quality and patient outcomes.

#### Acceptance Criteria

1. WHEN a consultation is marked complete, THE System SHALL send a Review_Request to the Patient via WhatsApp
2. WHEN a Patient responds to a Review_Request, THE System SHALL store the review rating and comments in the Master_Database
3. WHEN a Prescription includes medication with a schedule, THE Reminder_Service SHALL calculate reminder times based on dosage frequency
4. WHEN a medication reminder time arrives, THE Reminder_Service SHALL send a reminder message to the Patient via WhatsApp
5. WHEN a Patient completes their medication course, THE Reminder_Service SHALL stop sending reminders for that medication

### Requirement 5: AI-Powered Doctor Dashboard and Analytics

**User Story:** As a Doctor, I want to query patient history conversationally and access analytics, so that I can make informed decisions quickly without navigating complex interfaces.

#### Acceptance Criteria

1. WHEN a Doctor accesses the Dashboard, THE System SHALL display an AI chatbot interface
2. WHEN a Doctor asks about a specific Patient's history, THE System SHALL query the Graph_Database via LLM and return relevant patient visits, diagnoses, and prescriptions
3. WHEN a Doctor asks about their own statistics, THE System SHALL query the Master_Database and return metrics like patient count, common diagnoses, and treatment patterns
4. WHEN a hospital administrator asks about hospital-wide analytics, THE System SHALL return aggregated metrics like patient volume, average age, department utilization, and doctor performance
5. WHEN a query requires patient-specific information, THE System SHALL verify the Doctor has authorization to access that Patient's records
6. WHEN the Dashboard chatbot responds, THE System SHALL cite data sources and provide confidence indicators for AI-generated insights

### Requirement 6: Multilingual Support

**User Story:** As a Patient in India, I want to interact with the System in my native language, so that I can communicate comfortably without language barriers.

#### Acceptance Criteria

1. WHEN a Patient selects a language, THE System SHALL maintain that language preference for all future interactions
2. WHEN the Transcription_Service processes audio, THE System SHALL detect the spoken language automatically
3. WHEN generating reminders or notifications, THE System SHALL use the Patient's preferred language
4. WHEN a Patient switches languages mid-conversation, THE System SHALL adapt to the new language

### Requirement 7: PDF Prescription Generation

**User Story:** As a Patient, I want to receive a professionally formatted prescription document, so that I can present it to pharmacies and maintain my medical records.

#### Acceptance Criteria

1. WHEN generating a prescription PDF, THE System SHALL include: patient name, age, sex, date, Doctor name, diagnosis, medicines with dosage and duration, and medical notes
2. WHEN generating a prescription PDF, THE System SHALL include hospital branding and contact information
3. WHEN a prescription PDF is generated, THE System SHALL ensure the file size is under 2MB for WhatsApp compatibility
4. THE System SHALL generate prescription PDFs in the Patient's preferred language
5. WHEN a Patient requests a previous prescription, THE System SHALL retrieve and resend the stored PDF via WhatsApp

## Why AI is Essential

This system demonstrates meaningful AI use in several critical areas:

1. **Handwriting Recognition**: Traditional rule-based OCR cannot handle the variability in doctor handwriting. Deep learning models trained on medical handwriting are essential for accurate extraction.

2. **Natural Language Understanding**: Patients describe symptoms in varied, conversational language across multiple languages. AI-powered NLU extracts structured medical information from unstructured text, which rule-based systems cannot achieve.

3. **Conversational Querying**: The Dashboard chatbot uses LLMs to understand natural language queries and translate them into database queries. This enables doctors to ask "When did patient XYZ last visit?" instead of learning complex query syntax.

4. **Audio Transcription**: Converting multilingual audio to text requires sophisticated speech recognition models that handle accents, medical terminology, and background noise.

5. **Semantic Search**: The Graph_Database combined with LLM enables semantic understanding of medical relationships, allowing queries like "patients with similar symptoms" that go beyond keyword matching.

Without AI, this system would require rigid forms, manual data entry, and complex query interfaces that would not achieve the goal of reducing healthcare professional workload.
