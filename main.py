import os
import time
import logging
from datetime import datetime,  timedelta
from dotenv import load_dotenv
from googleapiclient.discovery import build
from slack_bolt import App
from google.oauth2.service_account import Credentials

load_dotenv()

logging.basicConfig(filename="slack_notifier.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID2")
SLACK_BOT_OAUTH_TOKEN = os.getenv("SLACK_BOT_OAUTH_TOKEN2")
app = App(token=SLACK_BOT_OAUTH_TOKEN)

def get_google_sheets_service():
    """Authenticate and return Google Sheets API service."""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SERVICE_ACCOUNT_FILE = "credentials.json"
    
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def read_from_google_sheet(sheet_id):
    """Reads Google Sheets data and returns it as a dictionary."""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()

    try:
        result = sheet.values().get(spreadsheetId=sheet_id, range="Sheet1!A1:E").execute()
        values = result.get("values", [])

        if not values:
            logging.info("No data found in the sheet.")
            return {}

        headers = values[0]  
        user_data = {row[0]: dict(zip(headers, row)) for row in values[1:]}  
        return user_data
    except Exception as e:
        logging.error(f"Error reading data from Google Sheets: {e}")
        return {}

def get_slack_user_id(email):
    """Fetches Slack user ID based on email."""
    try:
        response = app.client.users_lookupByEmail(email=email)
        return response["user"]["id"]
    except Exception as e:
        logging.error(f"Error fetching Slack user ID for {email}: {e}")
        return None

def send_notification(slack_user_ids, message):
    """Sends a Slack message to multiple users."""
    try:
        for slack_user_id in slack_user_ids:
            response = app.client.chat_postMessage(channel=slack_user_id, text=message)
            logging.info(f"Message sent to {slack_user_id}: {message}")
        return True
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

if __name__ == "__main__":
    users = read_from_google_sheet(SPREADSHEET_ID)
    user_ids = ['U07EC72AKQQ', 'U03L88SU78S']
    today = f"{datetime.today().month}/{datetime.today().day}"
    logging.info(f"Today's Date: {today}")
    print('Todays Date:', today)
    for name, details in users.items():
        email = details.get("Email", "")
        Birthday_date = details.get("Birthday Date", "")
        anniversary_date = details.get("Anniversary Date", "")

        slack_user_id = get_slack_user_id(email)
        if not slack_user_id:
            logging.warning(f"Could not find Slack User ID for {email}")
            continue

        birthday_mm_dd = "/".join(str(int(x)) for x in Birthday_date.split("/")[:2]) if Birthday_date else None
        anniversary_mm_dd = "/".join(str(int(x)) for x in anniversary_date.split("/")[:2]) if anniversary_date else None
        logging.info(f"Checking for {email} - Birthday: {birthday_mm_dd}, Anniversary: {anniversary_mm_dd}")

        if anniversary_date:
            join_year = int(anniversary_date.split("/")[-1])
            years_completed = datetime.today().year - join_year
            logging.info(f"Years Completed: {years_completed}")

        if Birthday_date:
            three_days_before_birthday = datetime.strptime(Birthday_date, "%m/%d/%Y") - timedelta(days=3)
            three_days_before_birthday = three_days_before_birthday.strftime("%m/%d")
            three_days_before_birthday = "/".join(str(int(x)) for x in three_days_before_birthday.split("/"))
            print(three_days_before_birthday)
        
        if anniversary_date:
            three_days_before_anniversary = datetime.strptime(anniversary_date, "%m/%d/%Y") - timedelta(days=3)
            three_days_before_anniversary = three_days_before_anniversary.strftime("%m/%d")
            three_days_before_anniversary = "/".join(str(int(x)) for x in three_days_before_anniversary.split("/"))
            print(three_days_before_anniversary)

        if birthday_mm_dd == today:
            logging.info(f"Sending Birthday Message for {email}, {name}")
            birthday_message = f"Hey <@{user_ids[1]}>, <@{user_ids[0]}> Today is <@{slack_user_id}>'s Birthday! 🎉 Let's all wish them a fantastic day and a great year ahead! 🎂🎈\n\nFROM: Team - Blackbook Properties"
            send_notification(user_ids, birthday_message)

        if today == three_days_before_birthday:
            logging.info(f"Sending Birthday Reminder for {email}, {name}")
            reminder_message = f"Hey <@{user_ids[1]}>, <@{user_ids[0]}> Reminder: <@{slack_user_id}>'s Birthday is in 3 days! 🎉 Get ready to celebrate! 🎂🎈\n\nFROM: Team - Blackbook Properties"
            send_notification(user_ids, reminder_message)

        if anniversary_mm_dd == today:
            logging.info(f"Sending Anniversary Message for {email}, {name}")
            anniversary_message = f"Hey <@{user_ids[1]}>, <@{user_ids[0]}> Today is <@{slack_user_id}>'s Work Anniversary! 🎉 Let's all congratulate them on completing {years_completed} years with us! 🎂🎈\n\nFROM: Team - Blackbook Properties"
            send_notification(user_ids, anniversary_message)

        if today == three_days_before_anniversary:
            logging.info(f"Sending Anniversary Reminder for {email}, {name}")
            anniversary_reminder = f"Hey <@{user_ids[1]}>, <@{user_ids[0]}> Reminder: <@{slack_user_id}>'s Work Anniversary is in 3 days! 🎉 Let's get ready to celebrate! 🎂🎈\n\nFROM: Team - Blackbook Properties"
            send_notification(user_ids, anniversary_reminder)

        time.sleep(1)




 
        

    
    
   
    
        