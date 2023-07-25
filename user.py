import datetime

class User:
    def __init__(self, user_vk_id, first_name, last_name, sex, bdate, city):
        self.user_vk_id = user_vk_id
        self.first_name = first_name
        self.last_name = last_name
        self.sex = sex
        self.bdate = bdate
        self.city = city

    def __repr__(self):
        return f"{self.first_name} {self.last_name} {self.user_vk_id} {self.bdate} {self.city}"

    def calculate_age(self):
        if self.bdate:
            bdate = datetime.datetime.strptime(self.bdate, "%d.%m.%Y")
            today = datetime.date.today()
            age = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
            return age
        return None

    def is_data_complete(self):
        required_fields = [self.bdate, self.sex, self.city]
        return all(field is not None for field in required_fields)