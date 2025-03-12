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
    service = get_google_sheets_service()
    sheet = service.spreadsheets()

    try:
        
        result = (
            sheet.values()
            .get(spreadsheetId=sheet_id, range="Sheet1!A1:C")
            .execute()
        )
        values = result.get("values", [])
        return values
    except HttpError as e:
        print(f"An error occurred while reading data from Google Sheet: {e}")
        return []
    
def get_slack_user_id(email):
    try:
        response = app.client.users_lookupByEmail(email=email)
        return response["user"]["id"]
    except Exception as e:
        print(f"An error occurred while looking up user by email: {e}")
        return None
    
def send_direct_message(slack_user_id, message):
    try:
        response = app.client.chat_postMessage(channel=slack_user_id, text=message)
        return response
    except Exception as e:
        print(f"An error occurred while sending a direct message: {e}")
        return None

if __name__ == "__main__":
    data = read_from_google_sheet(SPREADSHEET_ID)
    emails, birthdays, join_dates = [], [] , []
    # mention the user in the message like @user
    message= f'''Happy Birthday! 🎉🎂🎈, Have a Great Day
    
    
    FROM: Team - Blackbook Properties
    '''
    for row in data[1:]:
        emails.append(row[0])
        birthdays.append(row[1])
        join_dates.append(row[2])
    print("Emails: ", emails)
    print("Birthdays: ", birthdays)
    print("Join Dates: ", join_dates)
    for email in emails:
        slack_user_id = get_slack_user_id(email)
        print(f"Email: {email} => Slack User ID: {slack_user_id}")
        time.sleep(1)
        if slack_user_id:
            try:
                response = send_direct_message(slack_user_id, message)
                print(f"Message sent to {email} with Slack User ID {slack_user_id}: {response}")
            except Exception as e:
                print(f"An error occurred while sending a direct message: {e}")
        else:
            print(f"Could not find Slack User ID for {email}")
            


   

    