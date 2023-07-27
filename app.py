from flask import Flask, request, jsonify
from vk_api import VKAPI
from vk_chatbot import VKChatBot
import os
from dotenv import load_dotenv

# Load VK API tokens from the keys.env file
load_dotenv(dotenv_path=r'C:\Users\wangr\PycharmProjects\pythonProject7\keys.env')
vk_app_access_token = os.getenv('VK_API_TOKEN')
load_dotenv(dotenv_path=r'C:\Users\wangr\PycharmProjects\pythonProject7\keys_chat.env')
vk_chatbot_access_token = os.getenv('CHAT_TOKEN')

if not vk_app_access_token:
    raise ValueError("VK_API_TOKEN not found in environment variables.")

if not vk_chatbot_access_token:
    raise ValueError("CHAT_TOKEN not found in environment variables.")

# Create VKAPI instance for the application with the loaded token
vk_app_api = VKAPI(vk_app_access_token)

# Create VKAPI instance for the chatbot with the loaded token
vk_chatbot_api = VKAPI(vk_chatbot_access_token)

# Create the Flask app
app = Flask(__name__)

# Create the VKChatBot instance with the VKAPI for the chatbot
vk_chatbot = VKChatBot(vk_chatbot_api)

@app.route("/", methods=["POST"])
def handle_message():
    data = request.json
    if data.get("type") == "message_new":
        message = data.get("object", {}).get("message", {}).get("text")
        if message:
            vk_chatbot.handle_message(message)
    elif data.get("type") == "confirmation":
        return "cc0b5b06"  # Return the correct confirmation code
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()