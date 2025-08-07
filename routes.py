from flask import redirect, render_template, jsonify, request
from controllers import *
import time

def configure_routes(app):
    # -- Главная страница --
    @app.get("/")
    def index():
        return redirect('/merge-files')


    # -- Объединить файлы --
    @app.get('/merge-files')
    def merge_files():
        return render_template('merge.html')

    @app.post('/merge-files')
    def send_merge_files():
        start_time = time.time()
        bitrix_file = request.files['bitrix_file']
        web_file = request.files['web_file']

        res = MergeController.merge(
            web_file=web_file,
            bitrix_file=bitrix_file
        )

        end_time = time.time()  # Засекаем время окончания выполнения
        execution_time = end_time - start_time  # Вычисляем время выполнения
        
        print(f"Функция send_merge_files выполнилась за {execution_time:.4f} секунд")
        return res

    # -- Форматировать файл --
    @app.get('/format-file')
    def format_file():
        return render_template('format.html')

    @app.post('/format-file')
    def send_format_file():
        pass


    # -- Документация --
    @app.get('/documentation')
    def documentation():
        return render_template('doc.html')


    @app.get('/download/<file_id>')
    def download_file(file_id):
        pass


