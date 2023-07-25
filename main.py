import os
from dotenv import load_dotenv
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
    user_info = vk_api.get_user_info_by_id(user_id)

    if user_info:
        print("User Information:")
        print(user_info)

        # Calculate age using the provided birthdate
        age = user_info.calculate_age()

        if age is None:
            print("Error: Birthdate not available.")
            return

        # Example search parameters, you can modify them as per your requirements
        search_params = {
            "sex": 2 if user_info.sex == 1 else 1,  # Female (1 for male, 2 for female)
            "age_from": age - 1,
            "age": age,
            "age_to": age + 1,
            "city": user_info.city["id"],
        }

        # Search users based on the modified search parameters
        search_results = vk_api.search_users(search_params, user_info)

        if search_results:
            print("Search Results:")
            for result in search_results:
                print(result)
        else:
            print("No users found matching the search criteria.")
    else:
        print("Error: User information not available.")

if __name__ == "__main__":
    main()
