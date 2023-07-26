from dotenv import load_dotenv
import os
from vk_api import VKAPI

def main():
    # Load VK API token from the keys.env file
    load_dotenv(dotenv_path=r'C:\Users\wangr\PycharmProjects\pythonProject7\keys.env')
    vk_access_token = os.getenv('VK_API_TOKEN')
    if not vk_access_token:
        raise ValueError("VK_API_TOKEN not found in environment variables.")

    # Create VKAPI instance with the loaded token
    vk_api = VKAPI(vk_access_token)

    # Example Usage
    user_id = "813472314"  # Replace with the VK user ID you want to search for

    try:
        vk_api.clear_database()  # Step 1: Clear the existing database
        vk_api.get_user_and_search_pairs(user_id)  # Steps 2, 3, 4, and 5: Get user info, search pairs, get photos, and save to database
    except Exception as e:
        print(f"Error during the main process: {e}")

if __name__ == "__main__":
    main()
