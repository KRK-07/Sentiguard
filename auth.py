import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow


CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]


def login_with_google():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=creds)
    user_info = service.userinfo().get().execute()
    return user_info
