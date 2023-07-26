class VKChatBot:
    def __init__(self, vk_api):
        self.vk_api = vk_api

    def handle_message(self, message):
        # Check if the message is the "find me a pair" command
        if message.lower() == "find me a pair":
            user_id = self.vk_api.get_user_id_from_message(message)
            if user_id:
                self.vk_api.clear_database()
                self.vk_api.get_user_and_search_pairs(user_id)
            else:
                print("Failed to get user ID from the message.")
