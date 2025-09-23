# Gyan Setu WhatsApp Bot

This is a Flask-based WhatsApp bot using Twilio.

## Deployment

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run locally:
   ```bash
   python app.py
   ```

3. Or deploy to Heroku/Render:
   - Upload this repo
   - Heroku/Render will detect the Procfile and run the app

4. In Twilio Console → WhatsApp Sandbox:
   - Set "When a message comes in" to:
     `https://<your-app-url>/whatsapp`
