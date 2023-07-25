import os
from dotenv import load_dotenv
from vk_api import VKAPI
from tqdm import tqdm

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
        user_info = vk_api.get_user_info_by_id(user_id)
    except ConnectionError as ce:
        print(f"Connection Error: {ce}")
        return
    except ValueError as ve:
        print(f"Value Error: {ve}")
        return

    if user_info is not None:
        print("User Information:")
        print(f"First Name: {user_info.first_name}")
        print(f"Last Name: {user_info.last_name}")
        print(f"id: {user_info.user_vk_id}")
        print(f"Birthday: {user_info.bdate}")
        print(f"Sex: {user_info.sex}")
        print(f"City: {user_info.city['title']}")
        print("-----------------------------")
        print("There is a search for a pair for the user...")
        print("---------------------------------------------")

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
        try:
            search_results = vk_api.search_users(search_params, user_info)
        except ConnectionError as ce:
            print(f"Connection Error while searching users: {ce}")
            return
        except ValueError as ve:
            print(f"Value Error while searching users: {ve}")
            return

        if search_results:
            total_users = len(search_results)
            print(f"The search is over, the number of users of the opposite sex is found: {total_users}")

            with open('vk_users.json', 'w', encoding='utf-8') as file:
                for user in tqdm(search_results):
                    # Write user data to the JSON file
                    file.write(str(user) + "\n")
        else:
            print("No users found matching the search criteria.")
    else:
        print("Error: User information not available.")

if __name__ == "__main__":
    main()