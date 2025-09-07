import smtplib
from email.mime.text import MIMEText
import json
import os

def get_email_config():
    """Get email configuration from a config file or use defaults"""
    config_file = "email_config.json"
    default_config = {
        "from_addr": "sentiguard11@gmail.com",
        "app_password": "zuujhfyhvogbhnaw",  # User needs to update this
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                # Merge with defaults in case some keys are missing
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error reading email config: {e}")
    
    # Create default config file
    with open(config_file, "w") as f:
        json.dump(default_config, f, indent=4)
    
    print(f"Created {config_file}. Please update the app_password field with your Gmail app password.")
    return default_config

def send_alert_email(to_addr, count):
    config = get_email_config()
    
    # Check if app password is still default
    if config["app_password"] == "YOUR_APP_PASSWORD_HERE":
        print("❌ Email not sent: Please update the app_password in email_config.json")
        print("To get a Gmail app password:")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Enable 2-factor authentication if not already enabled")
        print("3. Go to 'App passwords' and generate a new password for 'Mail'")
        print("4. Update the app_password in email_config.json with the generated password")
        return False

    message_body = (
        f"Dear Guardian,\n\n"
        f"This is an automated alert from SentiGuard.\n\n"
        f"The user's mood sentiment score dropped below -0.5 a total of {count} times recently. "
        f"This may indicate a period of sustained low mood or distress.\n\n"
        f"Please consider reaching out to check in and offer support.\n\n"
        f"If you have questions or need more information, please let us know.\n\n"
        f"Best regards,\n"
        f"SentiGuard"
    )

    try:
        msg = MIMEText(message_body)
        msg["Subject"] = "SentiGuard Alert: Mood Threshold Reached"
        msg["From"] = config["from_addr"]
        msg["To"] = to_addr

        with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"]) as server:
            server.login(config["from_addr"], config["app_password"])
            server.send_message(msg)
        
        print(f"✅ Alert email sent successfully to {to_addr}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Email authentication failed: {e}")
        print("The app password may be expired. Please generate a new one:")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Go to 'App passwords' and generate a new password")
        print("3. Update the app_password in email_config.json")
        return False
    except Exception as e:
        print(f"❌ Failed to send alert email: {e}")
        return False
