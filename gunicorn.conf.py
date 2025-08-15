def post_fork(server, worker):
    """
    Вызывается Gunicorn после форка воркера.

    Эта функция запускает фоновый поток для очистки данных в указанной директории.
    Поток не блокирует работу воркера (flask приложения для создания отчетов).

    Parameters:
        server (object): Объект сервера Gunicorn.
        worker (object): Объект воркера Gunicorn, который был создан.

    Returns:
        None
    """
    # Импорт внутри функции предотвращает циклические зависимости
    from app import DataCleaner
    from threading import Thread
    import os

    # Создание экземпляра DataCleaner с указанием папки для очистки
    cleaner = DataCleaner(
        folders=[os.environ.get('UPLOAD_FOLDER', 'uploads')],
        max_life_time=100
    )

    # Создание и запуск потока для выполнения метода clean_data
    cleaner_thread = Thread(target=cleaner.clean_data)
    cleaner_thread.daemon = True  # Поток будет завершён при выходе из программы
    cleaner_thread.start()
