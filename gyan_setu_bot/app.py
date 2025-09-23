from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Links & Messages
APK_LINK = "https://drive.google.com/file/d/1VX3UjUzZarArXWt4u3hdkYMla6Z7zTJX/view?usp=drivesdk"
EXE_TEXT = "💻 Windows EXE version is coming soon..."
GYAN_INFO = (
    "👋 Hey user! This is a platform created by *Team Hackers* for you all.\n\n"
    "✨ We will do our best to provide you the best service.\n\n"
    "📢 For more information, join our channel:\n"
    "https://whatsapp.com/channel/0029Vb7EwfHGk1FryYMPm33x"
)

# Store suggestion state
user_states = {}

MENU_TEXT = (
    "🙏 Welcome! Please choose an option:\n\n"
    "1️⃣ Download APK\n"
    "2️⃣ Download EXE (coming soon)\n"
    "3️⃣ About Gyan Setu\n"
    "4️⃣ Update Request"
)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    from_number = request.values.get('From', '')
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # If user was asked for suggestion
    if user_states.get(from_number) == "awaiting_suggestion":
        msg.body("✅ Thanks for your suggestion!\n\n" + MENU_TEXT)
        user_states[from_number] = None  # Reset state
        return str(resp)

    # Menu options
    if "1" in incoming_msg:
        msg.body(f"⬇️ Download APK: {APK_LINK}\n\n" + MENU_TEXT)
    elif "2" in incoming_msg:
        msg.body(EXE_TEXT + "\n\n" + MENU_TEXT)
    elif "3" in incoming_msg:
        msg.body(GYAN_INFO + "\n\n" + MENU_TEXT)
    elif "4" in incoming_msg:
        msg.body("✍️ Please write your suggestion:")
        user_states[from_number] = "awaiting_suggestion"
    else:
        msg.body(MENU_TEXT)

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
