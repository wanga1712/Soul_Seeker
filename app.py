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
vk_chatbot = VKChatBot()

@app.route("/", methods=["POST"])
def handle_message():
    data = request.data.decode('utf-8')  # Get the raw string data from the request
    vk_chatbot.set_vk_api_instance(vk_chatbot_api)  # Set the VKAPI instance for the VKChatBot
    vk_chatbot.handle_message(data)  # Pass the raw string data to the chatbot for processing

    # Respond with a success message
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run()
