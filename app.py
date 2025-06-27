from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import os

app = Flask(__name__)

# Set your Gemini API key
GEMINI_API_KEY = "Your Gemini API Key"
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Model configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 40,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# System prompt as Movie Expert
system_prompt = """
You are a world-class Movie Expert AI Assistant. You know everything about movies including:
- Movie recommendations by genre, actor, director, or mood.
- Detailed movie summaries, trivia, cast info, and ratings.
- Hidden gems, classic films, and upcoming releases.
- Cultural context and behind-the-scenes stories.

When replying:
- Be friendly, fun, and informative.
- Provide clear and concise movie suggestions or explanations.
- Suggest related movies if a user mentions liking a specific one.

If a movie doesn't exist or you don't know, be honest and helpful.
"""

# Initialize the base model
base_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction=system_prompt
)

# In-memory short-term memory per user
user_sessions = {}


# Function to get Gemini response with session history
def get_gemini_response(user_id, user_input):
    if user_id not in user_sessions:
        # Start new conversation with system prompt
        user_sessions[user_id] = base_model.start_chat(history=[])

    chat = user_sessions[user_id]

    try:
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        print("Error from Gemini:", e)
        return "Sorry, I couldn't process your movie request right now. Try again later."


# Flask route for WhatsApp bot
@app.route("/bot", methods=["POST"])
def bot():
    user_number = request.values.get('From')  # Unique ID for each WhatsApp user
    incoming_msg = request.values.get('Body', '').strip()
    print(f"Received from {user_number}: {incoming_msg}")

    if not incoming_msg:
        reply = "Please send a movie-related question or request!"
    else:
        reply = get_gemini_response(user_number, incoming_msg)

    print(f"Reply to send: {reply}")
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)


if __name__ == "__main__":
    app.run(port=5000)
