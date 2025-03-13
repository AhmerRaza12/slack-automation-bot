import requests
import json
import os 
import time
from datetime import datetime
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from slack_bolt import App
load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SLACK_BOT_OAUTH_TOKEN = os.getenv("SLACK_BOT_OAUTH_TOKEN")
app = App(token=SLACK_BOT_OAUTH_TOKEN)


def get_google_sheets_service():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=8080)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def read_from_google_sheet(sheet_id):
    """ Reads Google Sheets data and returns it as a dictionary. """
    service = get_google_sheets_service()
    sheet = service.spreadsheets()

    try:
        result = sheet.values().get(spreadsheetId=sheet_id, range="Sheet1!A1:C").execute()
        values = result.get("values", [])

        if not values:
            return {}

        headers = values[0]  # Column headers
        user_data = {row[0]: dict(zip(headers, row)) for row in values[1:]}  # Convert to dict

        return user_data
    except Exception as e:
        print(f"An error occurred while reading data from Google Sheets: {e}")
        return {}

    
def get_slack_user_id(email):
    try:
        response = app.client.users_lookupByEmail(email=email)
        return response["user"]["id"]
    except Exception as e:
        print(f"An error occurred while looking up user by email: {e}")
        return None
    
def send_notification(slack_user_id, message):
    """ Sends a Slack message to the user. """
    try:
        response = app.client.chat_postMessage(channel=slack_user_id, text=message)
        return response
    except Exception as e:
        print(f"An error occurred while sending a message: {e}")
        return None

if __name__ == "__main__":
    users = read_from_google_sheet(SPREADSHEET_ID)
    today = datetime.today().strftime("%#m/%#d")  # Windows format
    print(f"Today's Date: {today}")

    for email, details in users.items():
        slack_user_id = get_slack_user_id(email)
        if not slack_user_id:
            print(f"Could not find Slack User ID for {email}")
            continue

        birthday = details.get("Birthday", "")
        join_date = details.get("Join Date", "")

        birthday_mm_dd = "/".join(str(int(x)) for x in birthday.split("/")[:2]) if birthday else None
        join_mm_dd = "/".join(str(int(x)) for x in join_date.split("/")[:2]) if join_date else None

        print(f"Checking for {email} - Birthday: {birthday_mm_dd}, Join Date: {join_mm_dd}")

        if join_date:
            join_year = int(join_date.split("/")[-1])
            years_completed = datetime.today().year - join_year
            print(f"Years Completed: {years_completed}")

        if birthday_mm_dd == today:
            print(f"Sending Birthday Message to {email}")
            birthday_message = f"Hey <@{slack_user_id}>, Happy Birthday! 🎉🎂🎈 Have a Great Day!\n\nFROM: Team - Blackbook Properties"
            send_notification("#birthdays-and-anniversaries", birthday_message)

        if join_mm_dd == today:
            print(f"Sending Anniversary Message to {email}")
            anniversary_message = f"Hey <@{slack_user_id}>, Congratulations on your {years_completed}th anniversary! 🎉 You have been a great asset, and we are thankful for the work you put in. Hoping for many more successful years with you! 🚀\n\nFROM: Team - Blackbook Properties"
            send_notification("birthdays-and-anniversaries", anniversary_message)

        time.sleep(1)

   

    