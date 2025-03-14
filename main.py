import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from slack_bolt import App
from google.oauth2.service_account import Credentials

load_dotenv()

logging.basicConfig(filename="slack_notifier.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SLACK_BOT_OAUTH_TOKEN = os.getenv("SLACK_BOT_OAUTH_TOKEN")
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
        result = sheet.values().get(spreadsheetId=sheet_id, range="Sheet1!A1:C").execute()
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

def send_notification(slack_user_id, message):
    """Sends a Slack message to the user."""
    try:
        response = app.client.chat_postMessage(channel=slack_user_id, text=message)
        logging.info(f"Message sent to {slack_user_id}: {message}")
        return response
    except Exception as e:
        logging.error(f"Error sending message to {slack_user_id}: {e}")
        return None

if __name__ == "__main__":
    users = read_from_google_sheet(SPREADSHEET_ID)
    today = f"{datetime.today().month}/{datetime.today().day}" 
    logging.info(f"Today's Date: {today}")

    for email, details in users.items():
        slack_user_id = get_slack_user_id(email)
        if not slack_user_id:
            logging.warning(f"Could not find Slack User ID for {email}")
            continue

        birthday = details.get("Birthday", "")
        join_date = details.get("Join Date", "")

        birthday_mm_dd = "/".join(str(int(x)) for x in birthday.split("/")[:2]) if birthday else None
        join_mm_dd = "/".join(str(int(x)) for x in join_date.split("/")[:2]) if join_date else None

        logging.info(f"Checking for {email} - Birthday: {birthday_mm_dd}, Join Date: {join_mm_dd}")

        if join_date:
            join_year = int(join_date.split("/")[-1])
            years_completed = datetime.today().year - join_year
            logging.info(f"Years Completed: {years_completed}")

        if birthday_mm_dd == today:
            logging.info(f"Sending Birthday Message to {email}")
            birthday_message = f"Hey <@{slack_user_id}>, Happy Birthday! 🎉🎂🎈 Have a Great Day!\n\nFROM: Team - Blackbook Properties"
            send_notification("#birthdays-and-anniversaries", birthday_message)

        if join_mm_dd == today:
            logging.info(f"Sending Anniversary Message to {email}")
            anniversary_message = f"Hey <@{slack_user_id}>, Congratulations on your {years_completed}th anniversary! 🎉 You have been a great asset, and we are thankful for the work you put in. Hoping for many more successful years with you! 🚀\n\nFROM: Team - Blackbook Properties"
            send_notification("birthdays-and-anniversaries", anniversary_message)

        time.sleep(1)
    