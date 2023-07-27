from dotenv import load_dotenv
import os
from vk_api import VKAPI
from vk_chatbot import VKChatBot

def main():
    # Load VK API token from the keys.env file
    load_dotenv(dotenv_path=r'C:\Users\wangr\PycharmProjects\pythonProject7\keys.env')
    vk_access_token = os.getenv('VK_API_TOKEN')
    if not vk_access_token:
        raise ValueError("VK_API_TOKEN not found in environment variables.")

    # Create VKAPI instance with the loaded token
    vk_api = VKAPI(vk_access_token)

    # Create VKChatBot instance with the VKAPI
    vk_chatbot = VKChatBot(vk_api)

    # Example Usage: Simulate a message from the VK group
    incoming_message = "find me a pair"

    # Step 1: Receive a message from the user and handle it
    user_id = vk_chatbot.handle_message(incoming_message)

    # Step 2: Get data about the user using the received user ID
    user_info = vk_api.get_user_info_by_id(user_id)

    # Step 3: Search for a pair for the user based on the parameters
    search_results = vk_api.search_pairs_for_user(user_info)

    # Step 4: Get photos from the albums of eligible users
    eligible_users_photos = vk_api.get_photos_of_eligible_users(search_results)

    # Step 5: Save photos and data of the received users in PostgreSQL
    vk_api.save_data_and_photos_to_postgres(user_info, search_results, eligible_users_photos)

if __name__ == "__main__":
    main()
