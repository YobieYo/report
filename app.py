from flask import Flask, request
from routes import configure_routes
import os

class PrefixMiddleware:
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if self.prefix:
            environ['SCRIPT_NAME'] = self.prefix
            path_info = environ['PATH_INFO']
            if path_info.startswith(self.prefix):
                environ['PATH_INFO'] = path_info[len(self.prefix):]
        return self.app(environ, start_response)

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Получаем префикс из переменной окружения
    prefix = os.environ.get('SCRIPT_NAME', '')
    
    # Применяем middleware только если префикс указан
    if prefix:
        app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=prefix)

    os.environ['UPLOAD_FOLDER'] = 'uploads'
    configure_routes(app)
    return app



if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)