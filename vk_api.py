import datetime
import requests
import psycopg2
from user import User
import time
from tqdm import tqdm


class VKAPI:
    BASE_URL = "https://api.vk.com/method/"
    MAX_REQUESTS_PER_SECOND = 3
    MAX_PHOTOS_PER_USER = 1000

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

    def clear_database(self):
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="05321983"
        )

        try:
            cursor = conn.cursor()

            # Start a transaction for the atomic operation
            with conn:
                # Delete all records from 'user_photos' table
                delete_user_photos_query = "DELETE FROM user_photos"
                cursor.execute(delete_user_photos_query)

                # Delete all records from 'users' table
                delete_users_query = "DELETE FROM users"
                cursor.execute(delete_users_query)

            print("Database cleared successfully!")
        except Exception as e:
            print(f"Error while clearing the database: {e}")
        finally:
            conn.close()

    def get_user_and_search_pairs(self, user_vk_id):
        try:
            user_info = self.get_user_info_by_id(user_vk_id)
            if user_info is None:
                print(f"User info for user_vk_id: {user_vk_id} is not available. Skipping further processing.")
                return
        except ConnectionError as ce:
            print(f"Connection Error: {ce}")
            return
        except ValueError as ve:
            print(f"Value Error: {ve}")
            return
        except Exception as e:
            print(f"Unknown error: {e}")
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
                search_results = self.search_users(search_params, user_info)
            except ConnectionError as ce:
                print(f"Connection Error while searching users: {ce}")
                return
            except ValueError as ve:
                print(f"Value Error while searching users: {ve}")
                return

            if search_results:
                total_users = len(search_results)
                print(f"The search is over, the number of users of the opposite sex is found: {total_users}")

                # Save user information and photos to the PostgreSQL database
                for user in tqdm(search_results):
                    user_id = user["id"]
                    try:
                        # Extract and save user photos to the database
                        success = self.save_user_photos_to_db(user_id)
                        if success:
                            print(
                                f"User {user['First Name']} {user['Last Name']} information and photos saved to the database successfully!")
                        else:
                            print(
                                f"Failed to save user {user['First Name']} {user['Last Name']} information and photos to the database.")
                    except ConnectionError as ce:
                        print(f"Connection Error while saving data to the database: {ce}")
                    except ValueError as ve:
                        print(f"Value Error while saving data to the database: {ve}")
                    except Exception as e:
                        print(f"Unknown error while saving data to the database: {e}")
            else:
                print("No users found matching the search criteria.")

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
        except ConnectionError as ce:
            print(f"Connection Error while fetching user information: {ce}")
            return None
        except ValueError as ve:
            print(f"Value Error while fetching user information: {ve}")
            return None
        except Exception as e:
            print(f"Unknown error while fetching user information: {e}")
            return None

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

    def get_all_user_photos(self, user_vk_id):
        method = "photos.get"
        params = {
            "owner_id": user_vk_id,
            "album_id": "wall",
            "extended": 1,
            "photo_sizes": 1,
            "access_token": self.access_token,
            "v": "5.131",
            "count": 100,  # Set the number of photos to fetch per request (adjust as needed)
        }

        try:
            photos = []

            while True:
                response = self._make_request(method, params)

                if response is None or "items" not in response:
                    break  # No photos to fetch or error in response, exit the loop

                photos.extend(response["items"])

                # Check if there are more photos to fetch
                total_count = response["count"]
                fetched_count = len(photos)

                # Check if the user has more photos than the fetched_count
                if fetched_count >= total_count:
                    break  # All photos have been fetched, exit the loop

                # Update the "offset" in the params for the next request
                params["offset"] = fetched_count

                # Be a responsible API user and limit requests per second
                time.sleep(1 / self.MAX_REQUESTS_PER_SECOND)

            return photos
        except Exception as e:
            print(f"Error while fetching user photos: {e}")
            return []

    def save_user_photos_to_db(self, user_vk_id):
        user_info = self.get_user_info_by_id(user_vk_id)
        if user_info is None:
            print(
                f"Failed to save user {user_vk_id} information and photos to the database. Reason: User information not available.")
            return False

        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="05321983"
        )

        try:
            cursor = conn.cursor()

            # Start a transaction for the atomic operation
            with conn:
                # Check if the user already exists in the 'users' table based on the user_vk_id
                check_user_query = "SELECT * FROM users WHERE user_vk_id = %s"
                cursor.execute(check_user_query, (user_vk_id,))
                existing_user = cursor.fetchone()

                if existing_user:
                    # Update user information in the 'users' table if the user already exists
                    update_user_query = "UPDATE users SET first_name = %s, last_name = %s, sex = %s, bdate = %s, city = %s WHERE user_vk_id = %s"
                    cursor.execute(update_user_query, (
                        user_info.first_name,
                        user_info.last_name,
                        user_info.sex,
                        user_info.bdate,
                        user_info.city["title"] if user_info.city else None,
                        user_vk_id,
                    ))
                else:
                    # Insert user information into the 'users' table if the user does not exist
                    insert_user_query = "INSERT INTO users (user_vk_id, first_name, last_name, sex, bdate, city) VALUES (%s, %s, %s, %s, %s, %s)"
                    cursor.execute(insert_user_query, (
                        user_vk_id,
                        user_info.first_name,
                        user_info.last_name,
                        user_info.sex,
                        user_info.bdate,
                        user_info.city["title"] if user_info.city else None,
                    ))

                # Fetch all user photos from all albums
                all_photos = self.get_all_user_photos(user_vk_id)

                if not all_photos:
                    print(
                        f"Failed to save user {user_vk_id} information and photos to the database. Reason: No photos found.")
                    return False

                # Save user photos into the 'user_photos' table
                for photo in all_photos:
                    largest_size_url = max(photo["sizes"], key=lambda x: x["width"])["url"]
                    likes_count = photo["likes"]["count"]
                    comments_count = photo["comments"]["count"]
                    photo_date = datetime.datetime.fromtimestamp(photo["date"])

                    insert_photo_query = "INSERT INTO user_photos (user_vk_id, photo_url, likes_count, comments_count, photo_date) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(insert_photo_query, (
                        user_vk_id,
                        largest_size_url,
                        likes_count,
                        comments_count,
                        photo_date,
                    ))

            print(
                f"User {user_info.first_name} {user_info.last_name} information and photos saved to the database successfully!")
            return True
        except Exception as e:
            print(f"Error while saving data to the database: {e}")
            return False
        finally:
            conn.close()