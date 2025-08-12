from flask import redirect, render_template, jsonify, request, send_file, Blueprint, url_for
from controllers import *
from schemas import FormatSchema, MergeSchema, ErrorSchema
import os

def configure_routes(app):
    base = os.environ.get('BASE_URL')
    # ======================== Logic Routes ========================

    @app.post(f'/merge-files')
    def send_merge_files():
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
        print('пришел запрос на скачивание')
        link = request.args.get('link')
        print(f'ссылка = {link}')

        return send_file(
            f'uploads/{link}',
        )



    # ======================== Static Routes ========================

    # -- Главная страница --
    @app.get(f'/')
    def index():
        return redirect(f'/merge-files')
    
    # -- Объединить файлы --
    @app.get(f'/merge-files')
    def merge_files():
        return render_template('merge.html')
    
    # -- Форматировать файл --
    @app.get(f'/format-file')
    def format_file():
        return render_template('format.html')
    
    # -- Документация --
    @app.get(f'/documentation')
    def documentation():
        return render_template('doc.html')

