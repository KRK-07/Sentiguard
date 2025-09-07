# SentiGuard

SentiGuard is a desktop app that helps you understand your daily mood by analyzing what you type (and optionally your voice). It runs locally on your PC, signs in with Google, visualizes live mood trends, and can email a guardian if it detects sustained negative sentiment. For privacy, keystrokes are stored only on your machine and are automatically cleared when the app exits.

## 🚀 Features

- Real‑time sentiment from what you type (private, local processing)
- Live mood trend chart in a modern, dark-themed GUI (Tkinter + Matplotlib)
- Optional voice input with basic voice‑emotion cues (if a microphone is available)
- Guardian alerts via email when negative sentiment persists
- Google OAuth sign‑in; user profile reflected in the UI

## 🛠️ Install and Setup (Windows)

Prerequisites
- Windows 10/11, Python 3.9–3.12 (64‑bit recommended)
- Optional: Microphone for voice features
- A Google account (for OAuth) and a Gmail account with App Password (for alerts)

1) Clone the repository
    ```powershell
    git clone https://github.com/KRK-07/SentiGuard.git
    cd SentiGuard
    ```

2) (Recommended) Create and activate a virtual environment
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

3) Install Python packages
    ```powershell
    pip install -r requirements.txt
    ```
    Note: PyAudio is needed for microphone access and is easiest to install on Windows with pipwin:
    ```powershell
    pip install pipwin
    pipwin install pyaudio
    ```

4) Google OAuth setup
- Go to Google Cloud Console → Create a project → Configure OAuth consent screen (External) → Create OAuth Client ID (Desktop app).
- Download the credentials JSON and save it as `client_secret.json` in the project root (same folder as `main.py`).

5) First run
    ```powershell
    python main.py
    ```
- A browser window will prompt you to sign in with Google.
- The app creates `user_settings.json`. By default, `guardian_email` is set to your own email.
- To send alerts to someone else, edit `user_settings.json` and set `guardian_email` to your trusted contact’s email.

## 👨💻 Authors

Created by [Sannihith Madasu](https://github.com/sannihith-madasu) [KR Keshav](https://github.com/KRK-07)

## 🚦 Usage

- Home: Quick welcome and quote.
- Live Mood Trend: Real‑time line chart of sentiment scores from your recent typing.
- Sentiment Analysis: Current score with an at‑a‑glance mood state.
- Guardian Dashboard: Shows alert status and history. Alerts trigger when negative lines since last alert exceed a threshold.

Data files (auto‑managed)
- `keystrokes.txt`: Lines you typed (appends during use; auto‑cleared on exit)
- `alert_status.json`: Tracks the last processed line index to avoid duplicate alerts
- `alerts_log.json`: History of sent alerts
- `user_settings.json`: Your name, Google ID, and guardian email

## 🔒 Security & Privacy

- Keystrokes are saved locally and cleared automatically when the app closes.
- No cloud storage; sentiment analysis happens on your device.
- Pause/quit the app before typing sensitive information.

## 🧰 Troubleshooting

- PyAudio installation fails on Windows
   - Use `pipwin install pyaudio` after `pip install pipwin`.
- OAuth login fails / no browser opens
   - Ensure `client_secret.json` is in the project root and matches a Desktop OAuth client. Try another default browser.
- NLTK VADER download takes long
   - The first run downloads the `vader_lexicon`. Keep internet on for the initial run.
- No audio device / microphone not found
   - Voice features are optional; the app will still work for typing-based mood tracking.
- Anti‑virus flags keylogging
   - This app only logs completed lines and clears them on exit. Add a local exception if needed.

## 📣 Acknowledgments

Inspired by mental health support needs and modern on‑device AI tooling.
