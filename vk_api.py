import datetime
import requests
from user import User

class VKAPI:
    BASE_URL = "https://api.vk.com/method/"

    def __init__(self, access_token):
        self.access_token = access_token

    def _make_request(self, method, params):
        url = f"{self.BASE_URL}{method}"
        params["access_token"] = self.access_token
        params["v"] = "5.131"  # VK API version

        response = requests.get(url, params=params)
        response_json = response.json()

        if response.status_code != 200:
            raise ConnectionError(f"Error in VK API request: {response_json.get('error')}")

        return response_json.get("response")

    def get_user_info_by_id(self, user_vk_id):
        method = "users.get"
        params = {
            "user_ids": user_vk_id,
            "fields": "sex,bdate,city",
        }

        try:
            response = self._make_request(method, params)
            user_info = response[0]
            # Check if the user data contains all necessary fields
            if all(key in user_info for key in ["id", "first_name", "last_name", "sex", "bdate", "city"]):
                return User(
                    user_vk_id=user_info["id"],
                    first_name=user_info["first_name"],
                    last_name=user_info["last_name"],
                    sex=user_info["sex"],
                    bdate=user_info.get("bdate"),
                    city=user_info.get("city"),
                )
            else:
                print(f"Incomplete data for user with ID {user_vk_id}. Skipping...")
        except Exception as e:
            print(f"Error while getting user info: {e}")
        return None

    def search_users(self, search_params, user_info):
        method = "users.search"
        search_params["count"] = 1000  # Fetch the first 1000 users per request

        # Filter users based on the user_info
        if user_info.city and "id" in user_info.city:
            city_id = user_info.city["id"]
        else:
            print(f"City not available for user {user_info.user_vk_id}. Skipping...")
            return []

        if user_info.sex == 1:
            search_params["sex"] = 2
        elif user_info.sex == 2:
            search_params["sex"] = 1

        # Get the birth year from the bdate if available
        if user_info.bdate:
            try:
                bdate = datetime.datetime.strptime(user_info.bdate, "%d.%m.%Y")
                birth_year = bdate.year
            except ValueError:
                print(f"Invalid birthdate format for user {user_info.user_vk_id}. Skipping...")
                return []
        else:
            print(f"Birthdate not available for user {user_info.user_vk_id}. Skipping...")
            return []

        # Adjust age range for search based on the birth year
        # Search for users with the same birth year, or older by a year, or younger by a year
        age_from = birth_year - 1
        age_to = birth_year + 1

        try:
            # Fetch the first 1000 users who match the specified search parameters
            response = self._make_request(method, search_params)
            if response is None:
                print("VK API returned None for the search.")
                return []

            items = response.get("items", [])

            # Get detailed user information for all users who match the search parameters
            users = []
            for user in items:
                user_info = self.get_user_info_by_id(user["id"])
                if user_info and user_info.city and "id" in user_info.city and user_info.city["id"] == city_id:
                    # Check if the user's birth year matches the desired range
                    if user_info.bdate:
                        try:
                            user_birth_year = datetime.datetime.strptime(user_info.bdate, "%d.%m.%Y").year
                            if age_from <= user_birth_year <= age_to:
                                users.append(user_info)
                        except ValueError:
                            print(f"Invalid birthdate format for user {user_info.user_vk_id}. Skipping...")
                    else:
                        print(f"Birthdate not available for user {user_info.user_vk_id}. Skipping...")

            return users
        except Exception as e:
            print(f"Error while searching users: {e}")
            return []
