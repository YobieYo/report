from flask import redirect, render_template, jsonify, request, send_file
from .controllers import *
from .schemas import FormatSchema, MergeSchema, ErrorSchema
import os


def configure_routes(app):
    """
    Регистрирует маршруты Flask-приложения.

    Функция определяет обработчики для логических и статических маршрутов:
    - Логические маршруты обрабатывают POST-запросы (например, загрузку и обработку файлов).
    - Статические маршруты возвращают HTML-страницы или перенаправления.

    :param app: Экземпляр Flask-приложения.
    :type app: Flask
    """

    # ======================== Logic Routes ========================

    @app.post(f'/merge-files')
    def send_merge_files():
        """
        Обрабатывает POST-запрос на объединение двух файлов.

        Получает два файла из формы, выполняет валидацию,
        передаёт их в контроллер для обработки и возвращает результат в формате JSON.

        :return: Ответ в формате JSON с данными результата или ошибкой.
        """
        try:
            print('пришел запрос на merge')
            # - валидация -
            web_file = request.files['web_file']
            bitrix_file = request.files['bitrix_file']
            print('открыты файлы')
            data = MergeSchema(
                web_file=web_file.filename,
                bitrix_file=web_file.filename,
            )
            print('данные валидны')

            # - Передача данных в контроллер -
            response = MergeController.merge(
                web_file=web_file,
                bitrix_file=bitrix_file
            )

            return jsonify(response.model_dump())
        except Exception as e:
            response = ErrorSchema(
                message=str(e),
                code=400
            )
            return jsonify(response.model_dump())

    @app.post(f'/format-file')
    def send_format_file():
        """
        Обрабатывает POST-запрос на форматирование файла.

        Получает JSON-данные, выполняет валидацию и проверку расширения файла.

        :return: Ответ в формате JSON с данными результата или ошибкой.
        """
        try:
            # - валидация -
            data = FormatSchema(**request.get_json())
            data.validate_excel_extension()

        except Exception as e:
            error = ErrorSchema(
                message=str(e),
                code=400
            )
            return jsonify(error.model_dump())

    @app.get(f'/download')
    def download_file():
        """
        Обрабатывает GET-запрос для скачивания файла.

        Извлекает параметр `link` из URL и отправляет соответствующий файл из папки uploads.

        :return: Файл для скачивания.
        """
        link = request.args.get('link')
        return send_file(
            f'../uploads/{link}',
        )

    # ======================== Static Routes ========================

    # -- Главная страница --
    @app.get(f'/')
    def index():
        """
        Обрабатывает GET-запрос на главную страницу.

        Выполняет перенаправление на страницу `/merge-files`.

        :return: Перенаправление.
        """
        return redirect(f'/merge-files')

    # -- Объединить файлы --
    @app.get(f'/merge-files')
    def merge_files():
        """
        Возвращает HTML-шаблон для страницы объединения файлов.

        :return: HTML-страница.
        """
        return render_template('merge.html')

    # -- Форматировать файл --
    @app.get(f'/format-file')
    def format_file():
        """
        Возвращает HTML-шаблон для страницы форматирования файлов.

        :return: HTML-страница.
        """
        return render_template('format.html')

    # -- Документация --
    @app.get(f'/documentation')
    def documentation():
        """
        Возвращает HTML-шаблон для страницы документации.

        :return: HTML-страница.
        """
        return render_template('doc.html')


