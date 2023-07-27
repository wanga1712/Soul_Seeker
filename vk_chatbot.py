import re

class VKChatBot:
    def __init__(self, vk_api):
        self.vk_api = vk_api

    def handle_message(self, message):
        # Extract user ID from the incoming message
        user_id = self.extract_user_id_from_message(message)

        if user_id is None:
            print("Error: Failed to extract user ID from the message.")
            return

        try:
            self.vk_api.clear_database()  # Step 1: Clear the existing database
            self.vk_api.get_user_and_search_pairs(user_id)  # Steps 2, 3, 4, and 5: Get user info, search pairs, get photos, and save to database
        except Exception as e:
            print(f"Error during the main process: {e}")

    def extract_user_id_from_message(self, message):
        # Use regular expression to find the user ID in the message
        # Assuming the message format is like: "find me a pair user_id123456789"
        pattern = r"user_id(\d+)"
        match = re.search(pattern, message)

        if match:
            return match.group(1)
        else:
            return None
