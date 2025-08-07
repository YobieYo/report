from flask import Flask, jsonify
from db.database import db
from data_loaders.excel_loader.excel_loader import ExcelLoader
from routes import configure_routes
import os
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    os.environ['UPLOAD_FOLDER'] = 'uploads'
    
    # Инициализация базы данных
    db.init_app(app)
    
    # Создание таблиц при первом запуске
    with app.app_context():
        db.drop_all()
        db.create_all()
    
    configure_routes(app)

    migrate = Migrate(app, db)

    db.session.close_all()
    
    
    @app.get('/launch_test')
    def test_launch():
        loader = ExcelLoader(
            bitrix_path=r'demo_data\битрикс.xlsx',
            web_path=r'demo_data\Отчет(архивный) (5).xlsx'
        )

        return jsonify('данные загружены')

    @app.get('/reset')
    def reset_database():
        with app.app_context():
            db.drop_all()  # Удаляет все таблицы
            db.create_all()  # Создает их заново
            print("База данных очищена и пересоздана!")


    return app





if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)