import pytest
from app import create_app
import pytest
import os
import shutil
from werkzeug.datastructures import FileStorage
from pathlib import Path
import pandas as pd

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def setup_upload_folder():
    """Создает временную папку для загрузки файлов"""
    upload_folder = "test_uploads"
    os.makedirs(upload_folder, exist_ok=True)
    os.environ['UPLOAD_FOLDER'] = upload_folder
    yield upload_folder
    shutil.rmtree(upload_folder, ignore_ok=True)  # Очистка после тестов

@pytest.fixture
def mock_result_file(tmp_path):
    """Фикстура создает тестовый Excel-файл с результатом"""
    upload_folder = tmp_path / "uploads"
    upload_folder.mkdir()
    
    # Создаем тестовые данные
    data = {
        "Название": ["Тест 1", "Тест 2"],
        "Значение": [100, 200]
    }
    df = pd.DataFrame(data)
    
    # Сохраняем файл
    file_path = upload_folder / "dhfdf_результат.xlsx"
    df.to_excel(file_path, index=False)
    
    # Возвращаем путь к файлу
    return str(file_path)