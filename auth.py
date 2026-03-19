import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow


CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]


def login_with_google():
    """
    Login with Google OAuth. Falls back to offline mode if no internet.
    """
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        from googleapiclient.discovery import build
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        print(f"⚠️  Google login failed (offline mode): {e}")
        print("   Running in offline mode with default user")
        # Return a default offline user
        return {
            'id': 'offline_user',
            'email': 'offline@localhost',
            'name': 'Offline User',
            'picture': None
        }
