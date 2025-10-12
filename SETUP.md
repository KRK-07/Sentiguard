# SentiGuard Setup Instructions

## 🔧 **Initial Setup**

# SentiGuard Setup Instructions

## 🚀 **Quick Setup (Recommended)**

### **1. Clone and Setup**
```bash
git clone https://github.com/KRK-07/sentiguard.git
cd sentiguard

# Run the automated setup script
python setup.py
```

### **2. Configure API Keys**
```bash
# Edit the .env file and add your API key:
# GEMINI_API_KEY=your_actual_api_key_here
```

### **3. Configure Google OAuth**
```bash
# Edit client_secret.json with your Google Cloud credentials
```

### **4. Run the Application**
```bash
# Activate virtual environment (if not already activated)
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Run SentiGuard
python main.py
```

---

## 🔧 **Manual Setup (Alternative)**

### **1. Clone the Repository**
```bash
git clone https://github.com/KRK-07/sentiguard.git
cd sentiguard
```

### **2. Create Virtual Environment**
```bash
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Setup Configuration Files**
```bash
# Copy template files
cp .env.template .env
cp client_secret.json.template client_secret.json
cp mood_history.json.template mood_history.json
cp user_settings.json.template user_settings.json
cp email_config.json.template email_config.json
cp alert_status.json.template alert_status.json

# Edit .env and add your API keys
# Edit client_secret.json with your Google Cloud credentials
```

### **5. Run the Application**
```bash
python main.py
```

## 🔑 **Getting API Keys**

### **Google Gemini API Key**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key or use existing one
3. Copy the API key to your `.env` file

### **Google OAuth Credentials**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Download `client_secret.json` and place in project root

## 🚀 **Running the Application**

```bash
# Make sure virtual environment is activated
python main.py
```

## 📁 **Project Structure**

```
sentiguard/
├── main.py                 # Application entry point
├── gui.py                  # Main GUI interface
├── auth.py                 # Authentication handling
├── analyzer.py             # Sentiment analysis engine
├── enhanced_analyzer.py    # Advanced context-aware analysis
├── ai_companion.py         # AI chatbot functionality
├── personalized_insights.py # AI insights generation
├── keylogger.py           # Keystroke monitoring
├── voice_recorder.py      # Voice emotion analysis
├── mailer.py              # Email notifications
├── mood_background.py     # Mood-responsive backgrounds
├── enhanced_mood_bg.py    # Advanced background effects
├── requirements.txt       # Python dependencies
├── .env.template          # Environment variables template
├── client_secret.json.template # OAuth credentials template
└── README.md              # Project documentation
```

## ⚠️ **Security Important Notes**

### **Files to NEVER commit:**
- `.env` (contains API keys)
- `client_secret.json` (contains OAuth secrets)
- `token.pickle` (contains user auth tokens)
- `keystrokes.txt` (contains sensitive user data)

### **Template files (safe to commit):**
- `.env.template`
- `client_secret.json.template`

## 🛠️ **Development**

### **Adding New Environment Variables**
1. Add to `.env.template` with placeholder value
2. Add to `.env` with actual value
3. Update this README with setup instructions

### **Testing**
```bash
# Run test suite (if available)
python -m pytest tests/

# Manual testing
python test_enhanced.py
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **"No module named 'google.generativeai'"**
   - Run: `pip install google-generativeai`

2. **"API key not found"**
   - Check `.env` file exists and contains `GEMINI_API_KEY`
   - Verify API key is valid at Google AI Studio

3. **OAuth authentication fails**
   - Verify `client_secret.json` has correct credentials
   - Check if Google+ API is enabled in Google Cloud Console

4. **Import errors**
   - Make sure virtual environment is activated
   - Run `pip install -r requirements.txt`

## 📞 **Support**

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Verify all setup steps are completed correctly

## 🔒 **Privacy & Security**

- All sensitive data is stored locally
- API keys are kept in environment variables
- User keystroke data is processed locally and cleared on exit
- No personal data is transmitted to external servers except for AI API calls