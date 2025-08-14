from threading import Thread
from app import create_app, DataCleaner
import os


# === Точка входа для запуска приложения во время отладки ===
if __name__ == '__main__':
    # Запускаем уборщик данных в отдельном потоке
    cleaner = DataCleaner(
        folders=[os.environ.get('UPLOAD_FOLDER', 'uploads')],
        max_life_time=100
    )
    cleaner_thread = Thread(target=cleaner.clean_data)
    cleaner_thread.daemon = True
    cleaner_thread.start(),

    # Запускаем приложение 
    app = create_app()
    app.run(debug=False)