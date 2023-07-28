import datetime

class User:
    def __init__(self, user_vk_id, first_name, last_name, sex, bdate, city):
        """
        Инициализирует объект User с информацией о пользователе.

        Параметры:
            user_vk_id (int): VK ID пользователя.
            first_name (str): Имя пользователя.
            last_name (str): Фамилия пользователя.
            sex (int): Пол пользователя (1 - мужской, 2 - женский).
            bdate (str): Дата рождения пользователя в формате "дд.мм.гггг".
            city (dict): Словарь с информацией о городе пользователя.

        Возвращает:
            None
        """
        self.user_vk_id = user_vk_id
        self.first_name = first_name
        self.last_name = last_name
        self.sex = sex
        self.bdate = bdate
        self.city = city

    def __repr__(self):
        """
        Возвращает строковое представление объекта User.

        Возвращает:
            str: Строковое представление объекта User.
        """
        return f"{self.first_name} {self.last_name} {self.user_vk_id} {self.bdate} {self.city}"

    def calculate_age(self):
        """
        Рассчитывает возраст пользователя на основе указанной даты рождения.

        Возвращает:
            int: Возраст пользователя или None, если дата рождения недоступна.
        """
        if self.bdate:
            bdate = datetime.datetime.strptime(self.bdate, "%d.%m.%Y")
            today = datetime.date.today()
            age = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
            return age
        return None

    def is_data_complete(self):
        """
        Проверяет, содержит ли объект User полную информацию о пользователе.

        Возвращает:
            bool: True, если информация полная, и False в противном случае.
        """
        required_fields = [self.bdate, self.sex, self.city]
        return all(field is not None for field in required_fields)
