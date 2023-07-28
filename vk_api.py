import datetime
import requests
import psycopg2
from user import User
import time
from tqdm import tqdm


class VKAPI:
    """
    Класс для взаимодействия с API ВКонтакте.

    Параметры:
        vk_access_token (str): Токен для доступа к API ВКонтакте.

    Атрибуты:
        BASE_URL (str): Базовый URL для API ВКонтакте.
        MAX_REQUESTS_PER_SECOND (int): Максимальное количество запросов в секунду к API ВКонтакте.
        MAX_PHOTOS_PER_USER (int): Максимальное количество фотографий пользователя для поиска.

    Методы:
        _make_request(method, params): Отправляет GET-запрос к API ВКонтакте и обрабатывает ответ.
        listen_for_messages(): Запускает прослушивание новых сообщений от пользователей.
        lookup_user_id_by_name(user_name): Ищет и возвращает VK ID пользователя по его имени.
        send_message(user_id, message, top_3_photos): Отправляет сообщение с указанным текстом и топ-3 фотографиями пользователю.
        clear_database(): Очищает базу данных от сохраненных пользователей и их фотографий.
        get_user_and_search_pairs(user_vk_id): Получает информацию о пользователе и ищет совместимые пары.
        get_user_info_by_id(user_vk_id): Получает информацию о пользователе по его VK ID.
        search_users(search_params, user_info, max_users=1000): Ищет пользователей по указанным параметрам.
        get_all_user_photos(user_vk_id): Получает все фотографии пользователя.
        save_user_photos_to_db(user_vk_id): Сохраняет информацию о пользователе и его фотографии в базу данных.
        send_top_photos_to_user(user_vk_id, user_info): Отправляет топ-3 популярных фотографии пользователю.
    """
    BASE_URL = "https://api.vk.com/method/"
    MAX_REQUESTS_PER_SECOND = 3
    MAX_PHOTOS_PER_USER = 1000

    def __init__(self, vk_access_token):
        """
        Инициализирует объект VKAPI с переданным токеном доступа VK.

        Параметры:
            vk_access_token (str): Токен доступа VK API.

        Возвращает:
            None
        """
        self.access_token = vk_access_token
        self.session = requests.Session()

    def _make_request(self, method, params):
        """
        Отправляет GET-запрос к API ВКонтакте и обрабатывает ответ.

        Параметры:
            method (str): Название метода API ВКонтакте.
            params (dict): Параметры запроса к API ВКонтакте.

        Возвращает:
            dict: Результат запроса в формате JSON.

        Исключения:
            ConnectionError: Если произошла ошибка при подключении к API ВКонтакте.
        """
        url = f"{self.BASE_URL}{method}"
        params["access_token"] = self.access_token
        params["v"] = "5.131"

        response = self.session.get(url, params=params)
        response_json = response.json()

        if response.status_code != 200:
            raise ConnectionError(f"Ошибка в запросе к API ВКонтакте: {response_json.get('error')}")

        return response_json.get("response")

    def listen_for_messages(self):
        """
        Запускает прослушивание новых сообщений от пользователей.

        Обработка сообщений выполняется в методе process_user_message().
        Если произошла ошибка при прослушивании или отправке сообщений, она будет выведена в консоль.
        """
        api_version = "5.131"
        url = f"https://api.vk.com/method/messages.getLongPollServer"
        params = {
            "access_token": self.access_token,
            "v": api_version,
        }

        try:
            response = requests.get(url, params=params)
            response_data = response.json()
            if "response" in response_data:
                server = response_data["response"]["server"]
                key = response_data["response"]["key"]
                ts = response_data["response"]["ts"]

                # Continuously poll for new messages
                while True:
                    longpoll_url = f"{server}?act=a_check&key={key}&ts={ts}&wait=25"
                    longpoll_response = requests.get(longpoll_url)
                    longpoll_data = longpoll_response.json()

                    if "failed" in longpoll_data:
                        # If long polling fails, reset the connection and continue
                        if longpoll_data["failed"] == 1:
                            ts = longpoll_data["ts"]
                        elif longpoll_data["failed"] in [2, 3]:
                            # Re-establish the long-polling connection
                            response = requests.get(url, params=params)
                            response_data = response.json()
                            if "response" in response_data:
                                server = response_data["response"]["server"]
                                key = response_data["response"]["key"]
                                ts = response_data["response"]["ts"]

                    elif "updates" in longpoll_data:
                        # Handle incoming messages
                        for update in longpoll_data["updates"]:
                            if update["type"] == "message_new":
                                user_id = update["object"]["message"]["from_id"]
                                message_text = update["object"]["message"]["text"]

                                # Process the user message and respond accordingly
                                self.process_user_message(user_id, message_text)

                                # Update the 'ts' value for the next long-polling request
                                ts = longpoll_data["ts"]

                    elif "type" in longpoll_data and longpoll_data["type"] == "confirmation":
                        # Return the confirmation string to verify the server
                        print("Для получения уведомлений нужно подтвердить адрес сервера.")
                        print("На него будет отправлен POST-запрос, содержащий JSON:")
                        print('{ "type": "confirmation", "group_id": 221730847 }')
                        return "a2da70b4"

        except Exception as e:
            print(f"Ошибка при прослушивании сообщений: {e}")

    def lookup_user_id_by_name(self, user_name):
        """
        Ищет и возвращает VK ID пользователя по его имени.

        Параметры:
            user_name (str): Имя пользователя ВКонтакте.

        Возвращает:
            int: VK ID пользователя, если найден, или None, если пользователь не найден.

        Исключения:
            ConnectionError: Если произошла ошибка при подключении к API ВКонтакте.
        """
        method = "users.get"
        params = {
            "user_ids": user_name,
        }

        try:
            response = self._make_request(method, params)
            user_info = response[0]
            if all(key in user_info for key in ["id"]):
                return user_info["id"]
            return None
        except ConnectionError as ce:
            print(f"Ошибка подключения при поиске ID пользователя: {ce}")
            return None
        except ValueError as ve:
            print(f"Ошибка значения при поиске ID пользователя: {ve}")
            return None
        except Exception as e:
            print(f"Неизвестная ошибка при поиске ID пользователя: {e}")
            return None

    def send_message(self, user_id, message, top_3_photos):
        """
        Отправляет сообщение с указанным текстом и топ-3 фотографиями пользователю.

        Параметры:
            user_id (int): VK ID пользователя, которому отправляется сообщение.
            message (str): Текст сообщения для отправки.
            top_3_photos (list): Список с URL топ-3 фотографий.

        Исключения:
            requests.RequestException: Если произошла ошибка при отправке сообщения.
        """
        api_version = "5.131"
        url = f"https://api.vk.com/method/messages.send"
        params = {
            "user_id": user_id,
            "message": message,
            "v": api_version,
            "access_token": self.access_token,
            "random_id": 0
        }

        try:
            response = requests.post(url, params=params)
            response_data = response.json()
            if "error" in response_data:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {response_data['error']['error_msg']}")
            else:
                print(f"Сообщение отправлено пользователю {user_id}: {message}")

            # Отправляем топ-3 фотографии как отдельные сообщения пользователю
            for i, photo in enumerate(top_3_photos, 1):
                photo_message = f"Топ-3 Фото {i}:\n{photo['photo_url']}"
                params["message"] = photo_message
                response = requests.post(url, params=params)
                response_data = response.json()
                if "error" in response_data:
                    print(
                        f"Не удалось отправить фото {i} пользователю {user_id}: {response_data['error']['error_msg']}")
                else:
                    print(f"Фото {i} отправлено пользователю {user_id}: {photo['photo_url']}")

        except requests.RequestException as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    def clear_database(self):
        """
        Очищает базу данных от сохраненных пользователей и их фотографий.
        """
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password=""
        )

        try:
            cursor = conn.cursor()

            # Начинаем транзакцию для атомарной операции
            with conn:
                # Удаляем все записи из таблицы 'user_photos'
                delete_user_photos_query = "DELETE FROM user_photos"
                cursor.execute(delete_user_photos_query)

                # Удаляем все записи из таблицы 'users'
                delete_users_query = "DELETE FROM users"
                cursor.execute(delete_users_query)

            print("База данных успешно очищена!")
        except Exception as e:
            print(f"Ошибка при очистке базы данных: {e}")
        finally:
            conn.close()

    def get_user_and_search_pairs(self, user_vk_id):
        """
        Получает информацию о пользователе по его VK ID и выполняет поиск пары для него.

        Параметры:
            user_vk_id (int): VK ID пользователя.

        Возвращает:
            User: Объект User с информацией о пользователе или None, если информация не найдена.

        Исключения:
            ConnectionError: Если произошла ошибка при подключении к API ВКонтакте.
        """
        try:
            user_info = self.get_user_info_by_id(user_vk_id)
            if user_info is None:
                print(f"Информация о пользователе с VK ID: {user_vk_id} недоступна. Пропускаю дальнейшую обработку.")
                return
        except ConnectionError as ce:
            print(f"Ошибка подключения: {ce}")
            return
        except ValueError as ve:
            print(f"Ошибка значения: {ve}")
            return
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            return

        if user_info is not None:
            print("Информация о пользователе:")
            print(f"Имя: {user_info.first_name}")
            print(f"Фамилия: {user_info.last_name}")
            print(f"ID: {user_info.user_vk_id}")
            print(f"День рождения: {user_info.bdate}")
            print(f"Пол: {'Мужчина' if user_info.sex == 2 else 'Женщина'}")
            print(f"Город: {user_info.city['title']}")
            print("-----------------------------")
            print("Выполняется поиск пары для пользователя...")
            print("---------------------------------------------")

            # Рассчитываем возраст, используя предоставленную дату рождения
            age = user_info.calculate_age()

            if age is None:
                print("Ошибка: Дата рождения недоступна.")
                return

            # Пример параметров поиска, вы можете их изменить по своим требованиям
            search_params = {
                "sex": 2 if user_info.sex == 1 else 1,  # Женский пол (1 для мужчин, 2 для женщин)
                "age_from": age - 1,
                "age": age,
                "age_to": age + 1,
                "city": user_info.city["id"],
            }

            # Поиск пользователей на основе измененных параметров поиска
            try:
                search_results = self.search_users(search_params, user_info)
            except ConnectionError as ce:
                print(f"Ошибка подключения при поиске пользователей: {ce}")
                return
            except ValueError as ve:
                print(f"Ошибка значения при поиске пользователей: {ve}")
                return

            if search_results:
                total_users = len(search_results)
                print(f"Поиск завершен, найдено пользователей противоположного пола: {total_users}")

                # Сохранение информации о пользователе и фотографий в базу данных PostgreSQL
                for user in tqdm(search_results):
                    user_id = user["id"]
                    try:
                        # Извлечение и сохранение фотографий пользователя в базу данных
                        success = self.save_user_photos_to_db(user_id)
                        if success:
                            print(
                                f"Информация и фотографии пользователя {user['First Name']} {user['Last Name']} успешно сохранены в базу данных!")
                        else:
                            print(
                                f"Не удалось сохранить информацию и фотографии пользователя {user['First Name']} {user['Last Name']} в базу данных.")
                    except ConnectionError as ce:
                        print(f"Ошибка подключения при сохранении данных в базу данных: {ce}")
                    except ValueError as ve:
                        print(f"Ошибка значения при сохранении данных в базу данных: {ve}")
                    except Exception as e:
                        print(f"Неизвестная ошибка при сохранении данных в базу данных: {e}")
            else:
                print("Пользователи, соответствующие критериям поиска, не найдены.")

    def get_user_info_by_id(self, user_vk_id):
        """
        Получает информацию о пользователе по указанному VK ID.

        Параметры:
            user_vk_id (int): VK ID пользователя.

        Возвращает:
            User: Объект User с информацией о пользователе или None, если информация недоступна.

        Исключения:
            ConnectionError: Если произошла ошибка при подключении к API ВКонтакте.
        """
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
                return None  # Вернуть None, если данные о пользователе неполные
        except ConnectionError as ce:
            print(f"Ошибка подключения при получении информации о пользователе: {ce}")
            return None
        except ValueError as ve:
            print(f"Ошибка значения при получении информации о пользователе: {ve}")
            return None
        except Exception as e:
            print(f"Неизвестная ошибка при получении информации о пользователе: {e}")
            return None

    def search_users(self, search_params, user_info, max_users=1000):
        """
        Ищет пользователей с заданными параметрами поиска.

        Параметры:
            search_params (dict): Словарь с параметрами поиска.
            user_info (User): Объект User с информацией о пользователе, для которого выполняется поиск.
            max_users (int, optional): Максимальное количество пользователей для поиска. По умолчанию 1000.

        Возвращает:
            list: Список словарей с информацией о пользователях, соответствующих критериям поиска.

        Исключения:
            ConnectionError: Если произошла ошибка при подключении к API ВКонтакте.
        """
        method = "users.search"
        search_params["count"] = 1000

        if user_info.city and "id" in user_info.city:
            city_id = user_info.city["id"]
        else:
            return []  # Вернуть пустой список, если данные о городе недоступны

        if user_info.sex == 1:
            search_params["sex"] = 2
        elif user_info.sex == 2:
            search_params["sex"] = 1

        if user_info.bdate:
            try:
                bdate = datetime.datetime.strptime(user_info.bdate, "%d.%m.%Y")
                birth_year = bdate.year
            except ValueError:
                return []  # Вернуть пустой список, если ошибка в формате даты рождения
        else:
            return []  # Вернуть пустой список, если данные о дате рождения недоступны

        age_from = birth_year - 1
        age_to = birth_year + 1

        try:
            response = self._make_request(method, search_params)
            if response is None:
                return []  # Вернуть пустой список, если VK API не вернул результаты поиска

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
                            pass  # Игнорировать пользователей с некорректным форматом даты рождения
                    else:
                        pass  # Игнорировать пользователей без информации о дате рождения

            return users
        except Exception:
            return []  # Вернуть пустой список, если произошла ошибка при поиске пользователей

    def get_all_user_photos(self, user_vk_id):
        """
        Получает все фотографии пользователя из VK API и сохраняет их в базу данных.

        Параметры:
            user_vk_id (int): VK ID пользователя, фотографии которого будут сохранены.

        Возвращает:
            list: Список словарей с информацией о фотографиях пользователя.

        Исключения:
            ConnectionError: Если произошла ошибка при подключении к API ВКонтакте.
        """
        method = "photos.get"
        params = {
            "owner_id": user_vk_id,
            "album_id": "wall",
            "extended": 1,
            "photo_sizes": 1,
            "access_token": self.access_token,
            "v": "5.131",
            "count": 100,
            # Установите количество фотографий, которые необходимо получить за один запрос (можно изменить по необходимости)
        }

        try:
            photos = []

            while True:
                response = self._make_request(method, params)

                if response is None or "items" not in response:
                    break  # Нет фотографий для получения или ошибка в ответе, выйти из цикла

                photos.extend(response["items"])

                # Проверить, есть ли еще фотографии для получения
                total_count = response["count"]
                fetched_count = len(photos)

                # Проверить, если у пользователя больше фотографий, чем получено за запрос
                if fetched_count >= total_count:
                    break  # Все фотографии были получены, выйти из цикла

                # Обновить параметр "offset" для следующего запроса
                params["offset"] = fetched_count

                # Быть ответственным пользователем API и ограничить количество запросов в секунду
                time.sleep(1 / self.MAX_REQUESTS_PER_SECOND)

            return photos
        except Exception as e:
            print(f"Ошибка при получении фотографий пользователя: {e}")
            return []

    def save_user_photos_to_db(self, user_vk_id):
        """
        Сохраняет информацию и топ-фотографии пользователя в базу данных.

        Параметры:
            user_vk_id (int): VK ID пользователя, для которого сохраняется информация и фотографии.

        Возвращает:
            bool: True, если информация и фотографии успешно сохранены в базу данных, в противном случае False.

        Исключения:
            requests.RequestException: Если произошла ошибка при отправке сообщения.
        """
        user_info = self.get_user_info_by_id(user_vk_id)
        if user_info is None:
            print(
                f"Не удалось сохранить информацию и фотографии пользователя {user_vk_id} в базе данных. Причина: Информация о пользователе недоступна.")
            return False

        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="05321983"
        )

        try:
            cursor = conn.cursor()

            # Начать транзакцию для атомарной операции
            with conn:
                # Проверить, существует ли пользователь уже в таблице 'users' на основе user_vk_id
                check_user_query = "SELECT * FROM users WHERE user_vk_id = %s"
                cursor.execute(check_user_query, (user_vk_id,))
                existing_user = cursor.fetchone()

                if existing_user:
                    # Обновить информацию о пользователе в таблице 'users', если пользователь уже существует
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
                    # Вставить информацию о пользователе в таблицу 'users', если пользователь не существует
                    insert_user_query = "INSERT INTO users (user_vk_id, first_name, last_name, sex, bdate, city) VALUES (%s, %s, %s, %s, %s, %s)"
                    cursor.execute(insert_user_query, (
                        user_vk_id,
                        user_info.first_name,
                        user_info.last_name,
                        user_info.sex,
                        user_info.bdate,
                        user_info.city["title"] if user_info.city else None,
                    ))

                # Получить все фотографии пользователя из всех альбомов
                all_photos = self.get_all_user_photos(user_vk_id)

                if not all_photos:
                    print(
                        f"Не удалось сохранить информацию и фотографии пользователя {user_vk_id} в базу данных. Причина: Фотографии не найдены.")
                    return False

                # Сохранить фотографии пользователя в таблицу 'user_photos'
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
                f"Информация и фотографии пользователя {user_info.first_name} {user_info.last_name} успешно сохранены в базе данных!")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении данных в базу данных: {e}")
            return False
        finally:
            conn.close()

    def send_top_photos_to_user(self, user_vk_id, user_info):
        """
        Отправляет топ-3 популярных фотографии пользователю.

        Параметры:
            user_vk_id (int): VK ID пользователя, которому отправляются фотографии.
            user_info (User): Объект User с информацией о пользователе.

        Исключения:
            requests.RequestException: Если произошла ошибка при отправке сообщения.
        """

        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="05321983"
        )

        try:
            cursor = conn.cursor()

            # Получить топ-3 популярные профильные фотографии из таблицы 'user_photos' для заданного user_vk_id
            get_top_photos_query = """
                SELECT photo_url
                FROM user_photos
                WHERE user_vk_id = %s
                ORDER BY (likes_count + comments_count) DESC
                LIMIT 3;
            """
            cursor.execute(get_top_photos_query, (user_vk_id,))
            top_photos = cursor.fetchall()

            if not top_photos:
                print("У пользователя нет популярных фотографий.")
                return

            # Отправить сообщение пользователю
            # Включить топ-3 фотографии и ссылки на профиль в сообщение
            # Оформить сообщение по вашему желанию
            message = f"Привет, {user_info.first_name}! Вот топ-3 популярных профильных фотографии для вас:\n"
            for i, photo in enumerate(top_photos, 1):
                message += f"{i}. {photo[0]}\n"
            message += "\nПриятного знакомства! 🚀"

            # Отправить сообщение пользователю с помощью метода VK API для отправки сообщений
            self.send_message(user_vk_id, message)

        except Exception as e:
            print(f"Ошибка при отправке топ-фотографий пользователю: {e}")
        finally:
            conn.close()
