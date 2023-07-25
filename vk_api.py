import datetime
import requests
from user import User
import time

class VKAPI:
    BASE_URL = "https://api.vk.com/method/"
    MAX_REQUESTS_PER_SECOND = 3

    def __init__(self, access_token):
        self.access_token = access_token
        self.session = requests.Session()

    def _make_request(self, method, params):
        url = f"{self.BASE_URL}{method}"
        params["access_token"] = self.access_token
        params["v"] = "5.131"

        response = self.session.get(url, params=params)
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
                return None  # Return None if user data is incomplete
        except Exception:
            return None  # Return None if there's an error while getting user info

    def search_users(self, search_params, user_info, max_users=1000):
        method = "users.search"
        search_params["count"] = 1000

        if user_info.city and "id" in user_info.city:
            city_id = user_info.city["id"]
        else:
            return []  # Return an empty list if city data is not available

        if user_info.sex == 1:
            search_params["sex"] = 2
        elif user_info.sex == 2:
            search_params["sex"] = 1

        if user_info.bdate:
            try:
                bdate = datetime.datetime.strptime(user_info.bdate, "%d.%m.%Y")
                birth_year = bdate.year
            except ValueError:
                return []  # Return an empty list if there's an error in the birthdate format
        else:
            return []  # Return an empty list if birthdate data is not available

        age_from = birth_year - 1
        age_to = birth_year + 1

        try:
            response = self._make_request(method, search_params)
            if response is None:
                return []  # Return an empty list if VK API returns None for the search

            items = response.get("items", [])

            users = []
            for user in items:
                user_info = self.get_user_info_by_id(user["id"])
                if user_info and user_info.city and "id" in user_info.city and user_info.city["id"] == city_id:
                    if user_info.bdate:
                        try:
                            user_birth_year = datetime.datetime.strptime(user_info.bdate, "%d.%m.%Y").year
                            if age_from <= user_birth_year <= age_to:
                                user_dict = {
                                    "First Name": user_info.first_name,
                                    "Last Name": user_info.last_name,
                                    "id": user_info.user_vk_id,
                                    "Birthday": user_info.bdate,
                                    "Sex": user_info.sex,
                                    "City": user_info.city["title"]
                                }
                                users.append(user_dict)
                        except ValueError:
                            pass  # Ignore invalid birthdate format for a user
                    else:
                        pass  # Ignore users with no birthdate information

            return users
        except Exception:
            return []  # Return an empty list if there's an error while searching users