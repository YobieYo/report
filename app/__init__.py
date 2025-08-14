from flask import Flask, request
from .routes import configure_routes
import os
from typing import List
import time
from datetime import datetime, timedelta
from threading import Thread

class PrefixMiddleware:
    """
    Промежуточная программа (middleware) для добавления префикса к пути запроса.

    Эта middleware изменяет `SCRIPT_NAME` и `PATH_INFO` в WSGI-окружении,
    чтобы обеспечить корректное поведение приложения, если оно обслуживается под определённым URL-префиксом.

    Например, если приложение запускается на URL `/new_reports/`, а запросы приходят на URL `/new_reports/users`,

    :param app: Приложение WSGI, которое будет оборачиваться.
    :type app: callable
    :param prefix: Префикс URL, который будет добавляться к каждому пути. По умолчанию пустая строка.
    :type prefix: str
    """

    def __init__(self, app, prefix=''):
        """
        Инициализирует middleware.

        :param app: Приложение WSGI, которое будет оборачиваться.
        :param prefix: Префикс URL, который будет добавляться к каждому пути.
        """
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        """
        Вызывается при каждом входящем WSGI-запросе.

        Меняет `SCRIPT_NAME` и `PATH_INFO`, если путь начинается с указанного префикса.

        :param environ: Словарь WSGI-окружения.
        :type environ: dict
        :param start_response: Функция, которая начинает формирование HTTP-ответа.
        :type start_response: callable
        :return: Ответ от оборачиваемого приложения.
        :rtype: iterable
        """
        if self.prefix:
            environ['SCRIPT_NAME'] = self.prefix
            path_info = environ['PATH_INFO']
            if path_info.startswith(self.prefix):
                environ['PATH_INFO'] = path_info[len(self.prefix):]
        return self.app(environ, start_response)

class DataCleaner:
    """
    Класс для автоматической очистки старых файлов в указанных папках.

    Удаляет файлы, которые не изменялись дольше, чем `max_life_time` секунд.
    Работает в бесконечном цикле и запускает сканирование папок раз в 60 секунд.

    :param folders: Список путей к папкам, в которых будет производиться очистка.
    :type folders: List[str]
    :param max_life_time: Максимальное время жизни файла в секундах.
                          Файлы, модифицированные раньше, будут удалены.
    :type max_life_time: float
    """

    def __init__(self, folders: List[str], max_life_time: float):
        """
        Инициализирует экземпляр класса DataCleaner.

        :param folders: Список путей к папкам для очистки.
        :param max_life_time: Максимальное время жизни файла в секундах.
        """
        self.folders = folders
        self.max_life_time = max_life_time
        print('Создан уборщик данных')

    def clean_data(self):
        """
        Основной метод для выполнения очистки данных.

        Запускает бесконечный цикл, каждые 60 секунд сканирует все указанные папки,
        проверяет время последней модификации каждого файла и удаляет те,
        которые старше `max_life_time`.

        Обработка ошибок при удалении файлов производится на уровне исключений.
        """
        while True:
            print('запущен цикл уборщика данных')
            time.sleep(60)
            now = datetime.now()
            for folder in self.folders:
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if now - file_modified > timedelta(seconds=self.max_life_time):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                print('Не удалось удалить файл', file_path, e)


def create_app():
    """
    Создаёт и настраивает экземпляр Flask-приложения.

    Функция инициализирует приложение, устанавливает параметры конфигурации,
    регистрирует middleware для обработки URL-префиксов, а также настраивает маршруты.

    :return: Настраиваемое Flask-приложение.
    :rtype: Flask
    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Получаем префикс из переменной окружения SCRIPT_NAME
    prefix = os.environ.get('SCRIPT_NAME', '')

    # Если указан префикс — оборачиваем WSGI-приложение в middleware
    if prefix:
        app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=prefix)

    # Устанавливаем папку для загрузки файлов
    os.environ['UPLOAD_FOLDER'] = 'uploads'

    # Регистрируем маршруты
    configure_routes(app)

    return app



