from flask import redirect, render_template, jsonify, request, send_file
from controllers import *
from schemas import FormatSchema, MergeSchema, DownloadSchema, ErrorSchema, SuccesSchema
def configure_routes(app):

    # ======================== Logic Routes ========================

    @app.post('/merge-files')
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

    @app.post('/format-file')
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

    @app.get('/download')
    def download_file():
        print('пришел запрос на скачивание')
        link = request.args.get('link')
        upload_folder = os.environ.get('UPLOAD_FOLDER')
        print(f'ссылка = {link}')

        return send_file(
            f'uploads\\{link}',
        )



    # ======================== Static Routes ========================

    # -- Главная страница --
    @app.get("/")
    def index():
        return redirect('/merge-files')
    
    # -- Объединить файлы --
    @app.get('/merge-files')
    def merge_files():
        return render_template('merge.html')
    
    # -- Форматировать файл --
    @app.get('/format-file')
    def format_file():
        return render_template('format.html')
    
    # -- Документация --
    @app.get('/documentation')
    def documentation():
        return render_template('doc.html')

