import os
import json
import datetime
import locale
from flask import Flask, request, jsonify
import requests
import gspread
from google.oauth2.service_account import Credentials
from babel.dates import format_datetime
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from config import (
    GOOGLE_CREDENTIALS
)


# ========= CONFIG =========
WHATSAPP_TOKEN = "<YOUR_WHATSAPP_TOKEN>"

# PHONE_NUMBER_ID = "810864372104195"
PHONE_NUMBER_ID = "750846411455167"

VERIFY_TOKEN = "myapptoken"

SPREADSHEET_ID = "1LWhTGN3mNYqe7gtuRNAKBx8W87HtO5QmLPxv-8zWCc8"
SHEET_CALENDAR = "Calendar"
SHEET_STATE = "State"
PATIENT_NOTES_COLUMN = "Patient_Notes"

WORKING_DAYS_TO_GENERATE = 5
START_HOUR = 10
END_HOUR = 18
LUNCH_HOUR = 13
IST = "Asia/Kolkata"
HOLIDAYS = ["2025-08-29"]

# ========= GOOGLE SHEETS =========
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    GOOGLE_CREDENTIALS, scopes=SCOPES
)
client = gspread.authorize(creds)
ss = client.open_by_key(SPREADSHEET_ID)

def get_sheet(name):
    return ss.worksheet(name)

# ========= MESSAGES =========
TEXTS = {
    "en": {
        "greet": "👋 Welcome! Please choose your language:",
        "choose_slot": "📅 Choose your appointment slot:",
        "no_slots": "❌ No available slots right now.",
        "booked": "✅ Appointment booked for {date} at {time}.",
        "taken": "❌ Slot already taken, please pick again.",
        "start": "Please type 'hi' to start booking ✅",
        "status_help": "Please send your update like: status I have mild fever since morning",
        "status_saved": "📝 Your health update is saved for your appointment on {date} at {time}.",
        "status_not_allowed": "No active upcoming appointment found. You can send status updates after booking and before your appointment date."
    },
    "hi": {
        "greet": "👋 स्वागत है! कृपया अपनी भाषा चुनें:",
        "choose_slot": "📅 अपनी अपॉइंटमेंट स्लॉट चुनें:",
        "no_slots": "❌ अभी कोई स्लॉट उपलब्ध नहीं है।",
        "booked": "✅ आपकी अपॉइंटमेंट {date} को {time} पर बुक हो गई है।",
        "taken": "❌ यह स्लॉट पहले से बुक है, कृपया दूसरा चुनें।",
        "start": "कृपया बुकिंग शुरू करने के लिए 'hi' लिखें ✅",
        "status_help": "अपना अपडेट ऐसे भेजें: status सुबह से हल्का बुखार है",
        "status_saved": "📝 आपका हेल्थ अपडेट {date} को {time} वाली अपॉइंटमेंट के लिए सेव हो गया है।",
        "status_not_allowed": "कोई आने वाली अपॉइंटमेंट नहीं मिली। स्टेटस अपडेट बुकिंग के बाद और अपॉइंटमेंट की तारीख तक भेज सकते हैं।"
    }
}

LANG_OPTIONS = [
    {"id": "LANG|en", "title": "English", "description": "Proceed in English"},
    {"id": "LANG|hi", "title": "हिन्दी", "description": "हिंदी में जारी रखें"}
]

# ========= UTILS =========
# def pretty_date(iso_str, lang="en"):
#     d = datetime.datetime.strptime(iso_str, "%Y-%m-%d")
#     if lang == "hi":
#         return d.strftime("%d %B %Y")  # हिंदी महीनों के लिए सिस्टम locale की जरूरत
#     return d.strftime("%a, %d %b %Y")
def pretty_date(iso_str, lang="en"):
    d = datetime.datetime.strptime(iso_str, "%Y-%m-%d")
    tz = pytz.timezone("Asia/Kolkata")
    d = tz.localize(d)

    if lang == "hi":
        return format_datetime(d, "EEEE, d MMMM y", locale="hi_IN")
    else:
        return format_datetime(d, "EEE, d MMM y", locale="en_IN")


# ========= SHEET HELPERS =========
def init_sheets():
    try:
        ss.worksheet(SHEET_CALENDAR)
    except:
        ss.add_worksheet(SHEET_CALENDAR, rows="100", cols="5")
        sh = get_sheet(SHEET_CALENDAR)
        sh.append_row(["Date", "Time", "Status", "Patient", "Phone", "Notes", "Medicine", "Duration(Days)", "Schedule", "Last_Reminder_Sent", "Appointment_Status", "Doctor_Rating", "Hospital_Rating", "Review_Comments"])
    try:
        ss.worksheet(SHEET_STATE)
    except:
        ss.add_worksheet(SHEET_STATE, rows="100", cols="6")
        st = get_sheet(SHEET_STATE)
        st.append_row(["Phone", "State", "Date", "Time", "Lang", "Name"])

    ensure_calendar_column(PATIENT_NOTES_COLUMN)


def ensure_calendar_column(column_name):
    cal = get_sheet(SHEET_CALENDAR)
    headers = cal.row_values(1)
    if column_name not in headers:
        cal.add_cols(1)
        cal.update_cell(1, len(headers) + 1, column_name)


def parse_appointment_datetime(date_str, time_str):
    for fmt in ["%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M"]:
        try:
            dt = datetime.datetime.strptime(f"{date_str} {time_str}", fmt)
            return tz.localize(dt)
        except ValueError:
            continue
    return None


def append_patient_status_note(phone, note_text):
    ensure_calendar_column(PATIENT_NOTES_COLUMN)
    cal = get_sheet(SHEET_CALENDAR)
    headers = cal.row_values(1)
    rows = cal.get_all_records()
    now = datetime.datetime.now(tz)
    candidates = []

    for i, r in enumerate(rows, start=2):
        if r.get("Status") != "Busy":
            continue

        phone_value = str(r.get("Phone Number") or r.get("Phone") or "").strip()
        if phone_value != str(phone):
            continue

        appt_dt = parse_appointment_datetime(r.get("Date", ""), r.get("Time", ""))
        if not appt_dt:
            continue

        if appt_dt.date() < now.date():
            continue

        candidates.append((appt_dt, i, r))

    if not candidates:
        return False, None, None

    candidates.sort(key=lambda x: x[0])
    appt_dt, row_index, row_data = candidates[0]

    note_col = headers.index(PATIENT_NOTES_COLUMN) + 1
    existing_notes = str(row_data.get(PATIENT_NOTES_COLUMN, "")).strip()
    timestamp = now.strftime("%Y-%m-%d %I:%M %p")
    new_entry = f"[{timestamp}] {note_text}"
    updated_notes = new_entry if not existing_notes else f"{existing_notes}\n{new_entry}"
    cal.update_cell(row_index, note_col, updated_notes)

    return True, row_data.get("Date", ""), row_data.get("Time", "")

def get_state(phone):
    st = get_sheet(SHEET_STATE)
    records = st.get_all_records()
    for idx, row in enumerate(records, start=2):
        if str(row["Phone"]) == str(phone):
            return row, idx
    st.append_row([phone, "NEW", "", "", "en", ""])
    return {"Phone": phone, "State": "NEW", "Date": "", "Time": "", "Lang": "en", "Name": ""}, st.row_count

def set_state(phone, fields):
    st = get_sheet(SHEET_STATE)
    row, idx = get_state(phone)
    for col, key in enumerate(["Phone", "State", "Date", "Time", "Lang", "Name"], start=1):
        if key in fields:
            st.update_cell(idx, col, fields[key])

def get_available_slots():
    cal = get_sheet(SHEET_CALENDAR)
    rows = cal.get_all_records()
    slots = []
    for r in rows:
        if r["Status"] == "Available":
            slots.append((r["Date"], r["Time"]))
    return slots

def book_slot(date_iso, time, patient, phone):
    cal = get_sheet(SHEET_CALENDAR)
    rows = cal.get_all_records()
    for i, r in enumerate(rows, start=2):
        if r["Date"] == date_iso and r["Time"] == time and r["Status"] == "Available":
            cal.update_cell(i, 3, "Busy")
            cal.update_cell(i, 4, patient)
            cal.update_cell(i, 5, phone)
            return True
    return False

# ========= WHATSAPP HELPERS =========
def call_whatsapp(payload):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json=payload)
    print("WA RESPONSE:", r.text)

def send_text(to, body):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    call_whatsapp(payload)

def send_language_choice(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": TEXTS["en"]["greet"]},
            "action": {
                "button": "Choose",
                "sections": [
                    {"title": "Languages", "rows": LANG_OPTIONS}
                ]
            }
        }
    }
    call_whatsapp(payload)

def send_slots(to, lang="en"):
    slots = get_available_slots()
    if not slots:
        send_text(to, TEXTS[lang]["no_slots"])
        return


    rows = []
    for d, t in slots:
        # short_date = datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%d %b")
        d_obj = datetime.datetime.strptime(d, "%Y-%m-%d")
        tz = pytz.timezone("Asia/Kolkata")
        d_obj = tz.localize(d_obj)

        if lang == "hi":
            short_date = format_datetime(d_obj, "d MMM", locale="hi_IN")
        else:
            short_date = format_datetime(d_obj, "d MMM", locale="en_IN")

        rows.append({
            "id": f"SLOT|{d}|{t}",
            "title": f"{t} {short_date}",
            "description": f"{pretty_date(d, lang)}"
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": TEXTS[lang]["choose_slot"]},
            "action": {
                "button": "Select",
                "sections": [
                    {"title": "Available Slots", "rows": rows[:10]}
                ]
            }
        }
    }
    call_whatsapp(payload)

# ========= FLASK SERVER =========
app = Flask(__name__)

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "error", 403

# @app.route("/webhook", methods=["POST"])
# def webhook():
#     data = request.get_json()
#     print("Incoming:", json.dumps(data, indent=2))
#     changes = data.get("entry", [])[0].get("changes", [])[0].get("value", {})
#     messages = changes.get("messages", [])
#     if not messages:
#         return "ok", 200

#     msg = messages[0]
#     from_ = msg["from"]
#     profile_name = changes.get("contacts", [{}])[0].get("profile", {}).get("name", "Unknown")

#     state, _ = get_state(from_)
#     lang = state.get("Lang", "en")

#     if msg["type"] == "text":
#         body = msg["text"]["body"].lower()
#         if body in ["hi", "hello", "hey", "नमस्ते", "हाय"]:
#             set_state(from_, {"State": "ASKED_LANG"})
#             send_language_choice(from_)
#         else:
#             send_text(from_, TEXTS[lang]["start"])

#     elif msg["type"] == "interactive":
#         lr = msg["interactive"].get("list_reply")
#         if lr and lr["id"].startswith("LANG|"):
#             _, chosen_lang = lr["id"].split("|")
#             set_state(from_, {"Lang": chosen_lang, "State": "ASKED_SLOT"})
#             send_slots(from_, lang=chosen_lang)

#         elif lr and lr["id"].startswith("SLOT|"):
#             _, d, t = lr["id"].split("|")
#             success = book_slot(d, t, profile_name, from_)
#             if success:
#                 set_state(from_, {"State": "BOOKED", "Date": d, "Time": t})
#                 send_text(from_, TEXTS[lang]["booked"].format(date=pretty_date(d, lang), time=t))
#             else:
#                 send_text(from_, TEXTS[lang]["taken"])
#                 send_slots(from_, lang=lang)

#     return "ok", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Incoming:", json.dumps(data, indent=2))
    changes = data.get("entry", [])[0].get("changes", [])[0].get("value", {})
    messages = changes.get("messages", [])
    if not messages:
        return "ok", 200

    msg = messages[0]
    from_ = msg["from"]
    profile_name = changes.get("contacts", [{}])[0].get("profile", {}).get("name", "Unknown")

    state, _ = get_state(from_)
    lang = state.get("Lang", "en")

    if msg["type"] == "text":
        raw_body = msg["text"]["body"].strip()
        body = raw_body.lower()
        if body in ["hi", "hello", "hey", "नमस्ते", "हाय"]:
            set_state(from_, {"State": "ASKED_LANG"})
            send_language_choice(from_)
        elif state.get("State") == "WAITING_REVIEW_COMMENTS":
            # Handle review comments
            cal = get_sheet(SHEET_CALENDAR)
            rows = cal.get_all_records()
            for i, r in enumerate(rows, start=2):
                if r["Date"] == state.get("Date") and r["Time"] == state.get("Time"):
                    if body.upper() != "SKIP":
                        cal.update_cell(i, 14, body)  # Save review comments
                    send_text(from_, "Thank you for your feedback! 🙏")
                    set_state(from_, {"State": "COMPLETE"})
                    break
        elif body.startswith("status"):
            patient_note = raw_body[6:].strip(" :-")
            if not patient_note:
                send_text(from_, TEXTS[lang]["status_help"])
            else:
                saved, appt_date, appt_time = append_patient_status_note(from_, patient_note)
                if saved:
                    send_text(
                        from_,
                        TEXTS[lang]["status_saved"].format(
                            date=pretty_date(appt_date, lang),
                            time=appt_time
                        )
                    )
                else:
                    send_text(from_, TEXTS[lang]["status_not_allowed"])
        else:
            send_text(from_, TEXTS[lang]["start"])

    elif msg["type"] == "interactive":
        lr = msg["interactive"].get("list_reply")
        if lr and lr["id"].startswith("LANG|"):
            _, chosen_lang = lr["id"].split("|")
            set_state(from_, {"Lang": chosen_lang, "State": "ASKED_SLOT"})
            send_slots(from_, lang=chosen_lang)

        elif lr and lr["id"].startswith("SLOT|"):
            _, d, t = lr["id"].split("|")
            success = book_slot(d, t, profile_name, from_)
            if success:
                set_state(from_, {"State": "BOOKED", "Date": d, "Time": t})
                send_text(from_, TEXTS[lang]["booked"].format(date=pretty_date(d, lang), time=t))
            else:
                send_text(from_, TEXTS[lang]["taken"])
                send_slots(from_, lang=lang)

        elif lr and lr["id"].startswith("DR|"):  # Handle Doctor Rating
            _, date, time, rating = lr["id"].split("|")
            cal = get_sheet(SHEET_CALENDAR)
            rows = cal.get_all_records()
            for i, r in enumerate(rows, start=2):
                if r["Date"] == date and r["Time"] == time:
                    cal.update_cell(i, 12, rating)  # Save doctor rating
                    
                    # Send hospital rating request
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": from_,
                        "type": "interactive",
                        "interactive": {
                            "type": "list",
                            "header": {
                                "type": "text",
                                "text": "🏥 Hospital Rating"
                            },
                            "body": {
                                "text": "How would you rate our hospital facilities?"
                            },
                            "action": {
                                "button": "Rate Hospital",
                                "sections": [{
                                    "title": "Hospital Rating",
                                    "rows": [
                                        {"id": f"HR|{date}|{time}|5", "title": "⭐⭐⭐⭐⭐ Excellent"},
                                        {"id": f"HR|{date}|{time}|4", "title": "⭐⭐⭐⭐ Good"},
                                        {"id": f"HR|{date}|{time}|3", "title": "⭐⭐⭐ Average"},
                                        {"id": f"HR|{date}|{time}|2", "title": "⭐⭐ Fair"},
                                        {"id": f"HR|{date}|{time}|1", "title": "⭐ Poor"}
                                    ]
                                }]
                            }
                        }
                    }
                    call_whatsapp(payload)
                    break

        elif lr and lr["id"].startswith("HR|"):  # Handle Hospital Rating
            _, date, time, rating = lr["id"].split("|")
            cal = get_sheet(SHEET_CALENDAR)
            rows = cal.get_all_records()
            for i, r in enumerate(rows, start=2):
                if r["Date"] == date and r["Time"] == time:
                    cal.update_cell(i, 13, rating)  # Save hospital rating
                    send_text(from_, "Please provide any additional comments or feedback (type SKIP if none):")
                    set_state(from_, {"State": "WAITING_REVIEW_COMMENTS", "Date": date, "Time": time})
                    break

    return "ok", 200

tz = pytz.timezone("Asia/Kolkata")

def check_and_send_reminders():
    cal = get_sheet(SHEET_CALENDAR)
    rows = cal.get_all_records()
    now = datetime.datetime.now(tz)

    for i, r in enumerate(rows, start=2):  # start=2 because header is row 1
        if r["Status"] == "Busy":
            date_str = r["Date"]  # e.g., 2025-09-24
            time_str = r["Time"]  # e.g., 15:00
            dt = tz.localize(datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p"))


            patient = r["Patient Name"]
            phone = r["Phone Number"]

            # --- 24h reminder ---
            if "Reminder24Sent" in r and r["Reminder24Sent"] == "Yes":
                pass
            elif now + datetime.timedelta(hours=24) >= dt > now + datetime.timedelta(hours=23, minutes=55):
                send_text(phone, f"⏰ Reminder: Your appointment is tomorrow at {time_str} on {pretty_date(date_str)}.")
                cal.update_cell(i, 6, "Yes")  # assuming col 6 = Reminder24Sent

            # --- 1h reminder ---
            if "Reminder1hSent" in r and r["Reminder1hSent"] == "Yes":
                pass
            elif now + datetime.timedelta(hours=1) >= dt > now + datetime.timedelta(minutes=55):
                send_text(phone, f"⏰ Reminder: Your appointment is in 1 hour at {time_str} on {pretty_date(date_str)}.")
                cal.update_cell(i, 7, "Yes")  # assuming col 7 = Reminder1hSent
                

def set_medicine_details(date_iso, time, medicine, duration, schedule):
    cal = get_sheet(SHEET_CALENDAR)
    rows = cal.get_all_records()
    for i, r in enumerate(rows, start=2):
        if r["Date"] == date_iso and r["Time"] == time:
            try:
                # Update medicine details in sheet
                duration = str(duration).replace('days', '').strip()
                schedule = schedule.replace('-', '|').replace("'", '')
                
                cal.update_cell(i, 7, medicine)
                cal.update_cell(i, 8, duration)
                cal.update_cell(i, 9, schedule)
                cal.update_cell(i, 10, "")
                
                # Send initial prescription notification
                phone = r["Phone Number"]
                morning, afternoon, evening = schedule.split("|")[:3]
                
                msg = f"🏥 Your Prescription Details:\n\n"
                msg += f"Medicine: {medicine}\n"
                msg += f"Duration: {duration} days\n\n"
                msg += "Daily Schedule:\n"
                if morning == "1": msg += "- Morning: 9:00 AM (with breakfast)\n"
                if afternoon == "1": msg += "- Afternoon: 2:00 PM (with lunch)\n"
                if evening == "1": msg += "- Evening: 8:00 PM (with dinner)\n\n"
                msg += "You will receive reminders before each dose. 🕐"
                
                print(f"Sending initial prescription to {phone}")
                send_text(phone, msg)
                return True
            except Exception as e:
                print(f"Error in set_medicine_details: {e}")
                return False
    return False

def check_new_medicines():
    print("\n=== Checking for new medicine entries ===")
    cal = get_sheet(SHEET_CALENDAR)
    rows = cal.get_all_records()
    
    for i, r in enumerate(rows, start=2):
        try:
            if (r["Status"] == "Busy" and 
                r.get("Medicine") and 
                r.get("Schedule") and 
                not r.get("Last_Reminder_Sent")):  # No notification sent yet
                
                print(f"Found new medicine entry for {r['Patient Name']}")
                
                # Send initial notification
                phone = r["Phone Number"]
                schedule = str(r["Schedule"]).strip()
                morning, afternoon, evening = schedule.split("|")[:3]
                
                msg = f"🏥 Your Prescription Details:\n\n"
                msg += f"Medicine: {r['Medicine']}\n"
                msg += f"Duration: {r['Duration(Days)']} days\n\n"
                msg += "Daily Schedule:\n"
                if morning == "1": msg += "- Morning: 9:00 AM (with breakfast)\n"
                if afternoon == "1": msg += "- Afternoon: 2:00 PM (with lunch)\n"
                if evening == "1": msg += "- Evening: 8:00 PM (with dinner)\n\n"
                msg += "You will receive reminders before each dose. 🕐"
                
                print(f"Sending initial prescription to {phone}")
                send_text(phone, msg)
                
                # Mark as notified
                cal.update_cell(i, 10, "INITIAL_SENT")
                
        except Exception as e:
            print(f"Error checking new medicines: {e}")


def check_medicine_reminders():
    print("\n=== Medicine Reminder Check ===")
    cal = get_sheet(SHEET_CALENDAR)
    rows = cal.get_all_records()
    now = datetime.datetime.now(tz)
    
    for i, r in enumerate(rows, start=2):
        try:
            if r["Status"] == "Busy" and r.get("Medicine") and r.get("Schedule"):
                # Check if medicine duration is still valid
                appt_date = datetime.datetime.strptime(r["Date"], "%Y-%m-%d").date()
                duration = int(str(r["Duration(Days)"]).strip())
                end_date = appt_date + datetime.timedelta(days=duration)
                
                if now.date() > end_date:
                    continue
                    
                schedule = str(r["Schedule"]).strip()
                if "|" in schedule:
                    morning, afternoon, evening = schedule.split("|")[:3]
                    current_time = now.time()
                    last_reminder = r.get("Last_Reminder_Sent", "")
                    today_date = now.strftime("%Y-%m-%d")
                    
                    # Send reminders 15 minutes before each dose
                    if (morning == "1" and 
                        current_time.hour == 8 and 
                        45 <= current_time.minute <= 59 and
                        last_reminder != today_date + "_morning"):
                        send_text(r["Phone Number"], 
                            f"💊 Time for your morning medicine!\nPlease take {r['Medicine']} with breakfast at 9:00 AM")
                        cal.update_cell(i, 10, today_date + "_morning")
                    
                    elif (afternoon == "1" and 
                          current_time.hour == 13 and 
                          45 <= current_time.minute <= 59 and
                          last_reminder != today_date + "_afternoon"):
                        send_text(r["Phone Number"], 
                            f"💊 Time for your afternoon medicine!\nPlease take {r['Medicine']} with lunch at 2:00 PM")
                        cal.update_cell(i, 10, today_date + "_afternoon")
                    
                    elif (evening == "1" and 
                          current_time.hour == 19 and 
                          45 <= current_time.minute <= 59 and
                          last_reminder != today_date + "_evening"):
                        send_text(r["Phone Number"], 
                            f"💊 Time for your evening medicine!\nPlease take {r['Medicine']} with dinner at 8:00 PM")
                        cal.update_cell(i, 10, today_date + "_evening")
                    
        except Exception as e:
            print(f"Error in check_medicine_reminders: {e}") 

def check_completed_appointments():
    print("\n=== Checking for completed appointments ===")
    cal = get_sheet(SHEET_CALENDAR)
    rows = cal.get_all_records()
    
    for i, r in enumerate(rows, start=2):
        try:
            if (r["Status"] == "Busy" and 
                r.get("Appointment_Status") == "Done" and 
                not r.get("Doctor_Rating")):  # No review submitted yet
                
                print(f"Sending review form to {r['Patient Name']}")
                
                # Send review request via WhatsApp
                phone = r["Phone Number"]
                payload = {
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "interactive",
                    "interactive": {
                        "type": "list",
                        "header": {
                            "type": "text",
                            "text": "📋 Appointment Review"
                        },
                        "body": {
                            "text": f"Thank you for visiting us on {r['Date']} at {r['Time']}. Please rate your experience:"
                        },
                        "action": {
                            "button": "Rate Now",
                            "sections": [{
                                "title": "Doctor Rating",
                                "rows": [
                                    {"id": f"DR|{r['Date']}|{r['Time']}|5", "title": "⭐⭐⭐⭐⭐ Excellent"},
                                    {"id": f"DR|{r['Date']}|{r['Time']}|4", "title": "⭐⭐⭐⭐ Good"},
                                    {"id": f"DR|{r['Date']}|{r['Time']}|3", "title": "⭐⭐⭐ Average"},
                                    {"id": f"DR|{r['Date']}|{r['Time']}|2", "title": "⭐⭐ Fair"},
                                    {"id": f"DR|{r['Date']}|{r['Time']}|1", "title": "⭐ Poor"}
                                ]
                            }]
                        }
                    }
                }
                call_whatsapp(payload)
                
        except Exception as e:
            print(f"Error checking completed appointments: {e}")
                                                  
@app.route("/set_medicine", methods=["POST"])
def set_medicine():
    data = request.get_json()
    required = ["date_iso", "time", "medicine", "duration", "schedule"]  # Changed 'date' to 'date_iso'
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        success = set_medicine_details(
            date_iso=data["date_iso"],
            time=data["time"],
            medicine=data["medicine"],
            duration=data["duration"],
            schedule=data["schedule"]
        )
        
        if success:
            return jsonify({"status": "success"}), 200
        return jsonify({"error": "Appointment not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test_medicine_notification", methods=["GET"])
def test_medicine_notification():
    try:
        test_data = {
            "date_iso": "2025-11-05",
            "time": "8:20 AM",
            "medicine": "Test Medicine",
            "duration": "1",
            "schedule": "1|1|1"
        }
        success = set_medicine_details(**test_data)
        if success:
            return jsonify({"status": "Test medicine notification sent"}), 200
        return jsonify({"error": "Failed to send test notification"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_sheets()
    # Start background scheduler for reminders
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_and_send_reminders, trigger="interval", minutes=5)
    scheduler.add_job(func=check_medicine_reminders, trigger="interval", seconds=30)  # Add medicine reminder job
    scheduler.add_job(func=check_new_medicines, trigger="interval", seconds=30)  # Add this line
    scheduler.add_job(func=check_completed_appointments, trigger="interval", minutes=1)  # Add this line
    scheduler.start()

    
    # app.run(host="0.0.0.0", port=5000)
    port = int(os.environ.get("PORT", 5000))  # default 5000 for local
    app.run(host="0.0.0.0", port=port)

