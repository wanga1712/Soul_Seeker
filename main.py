import os
from dotenv import load_dotenv
from vk_api import VKAPI

def main():
    """
    Основной скрипт для запуска чат-бота VKinder.

    Использует токен VK API, который должен быть задан в файле keys.env.
    Создает экземпляр VKAPI для взаимодействия с API VK и обработки сообщений.
    Запускает прослушивание входящих сообщений от пользователей.

    Raises:
        ValueError: Если VK_API_TOKEN не найден в переменных окружения.
    """
    # Загрузка токена VK API из файла keys.env
    load_dotenv(dotenv_path=r'C:\Users\wangr\PycharmProjects\pythonProject7\keys.env')
    vk_app_access_token = os.getenv('VK_API_TOKEN')

    # Подтверждение токена VK API
    if not vk_app_access_token:
        raise ValueError("VK_API_TOKEN не найден в переменных окружения.")

    # Создание экземпляра VKAPI
    vk_api = VKAPI(vk_app_access_token)

    try:
        # Запуск прослушивания сообщений от пользователей
        while True:
            vk_api.listen_for_messages()

    except ValueError as ve:
        print(f"Ошибка: {ve}")
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")


if __name__ == "__main__":
    main()
