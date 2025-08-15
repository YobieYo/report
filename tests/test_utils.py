import os
import uuid
from typing import List, Tuple
import pytest
from unittest.mock import Mock, patch
from app.utils import Utils, ExcelUtils
import pandas as pd


class TestUtils:
    """
    Тесты для статических методов класса `Utils`.
    """

    @pytest.fixture
    def mock_upload_folder(self):
        """
        Фикстура, возвращающая временную папку для тестирования сохранения файлов.
        """
        return '/tmp/test_upload_folder'

    @pytest.fixture
    def mock_files(self):
        """
        Фикстура, имитирующая список загруженных файлов.
        """
        file1 = Mock()
        file1.filename = 'test_file1.txt'
        file1.save = Mock()

        file2 = Mock()
        file2.filename = 'test_file2.jpg'
        file2.save = Mock()

        return [file1, file2]

    def test_save_uploaded_files_saves_all_files_and_returns_paths(self, mock_upload_folder, mock_files):
        """
        Проверяет, что метод `save_uploaded_files` сохраняет все переданные файлы,
        присваивает им уникальные имена и возвращает кортеж из путей к файлам.
        """
        with patch('app.utils.uuid.uuid4', return_value='fixed-uuid-123'):
            result = Utils.save_uploaded_files(mock_files, mock_upload_folder)

            # Все файлы должны быть сохранены в указанную папку
            assert len(result) == 2
            assert all(path.startswith(mock_upload_folder) for path in result)
            
            # У всех файлов единый UUID префикс
            assert all('fixed-uuid-123' in path for path in result)
            
            # Новые имена файлов должны содержать оригинальные
            assert 'test_file1.txt' in result[0]
            assert 'test_file2.jpg' in result[1]
            
            # Файл должен быть сохранен лишь один раз
            for file in mock_files:
                file.save.assert_called_once()

    def test_save_uploaded_files_handles_empty_list_of_files(self, mock_upload_folder):
        """
        Проверяет, что метод `save_uploaded_files` корректно обрабатывает пустой список файлов.
        """
        result = Utils.save_uploaded_files([], mock_upload_folder)
        assert result == tuple()

    def test_create_save_file_generates_unique_path(self, mock_upload_folder):
        """
        Проверяет, что метод `create_save_file` генерирует уникальный путь с расширением .xlsx.
        """
        with patch('app.utils.uuid.uuid4', return_value='fixed-uuid-123'):
            path, filename = Utils.create_save_file(mock_upload_folder)

            assert path.endswith('.xlsx')
            assert filename.endswith('.xlsx')
            assert 'результат_' in filename
            assert 'fixed-uuid-123' in path

    def test_create_save_file_with_invalid_folder(self):
        """
        Проверяет, что метод `create_save_file` не создаёт файл при некорректной папке.
        В данном случае проверка только на формирование пути, а не на фактическое создание файла.
        """
        invalid_folder = '/invalid/path/that/does/not/exist'
        with patch('app.utils.uuid.uuid4', return_value='fixed-uuid-123'):
            path, filename = Utils.create_save_file(invalid_folder)

            assert path.startswith(invalid_folder)
            assert os.path.basename(path) == 'результат_fixed-uuid-123.xlsx'

    def test_create_save_file_with_long_uuid_does_not_break_path(self, mock_upload_folder):
        """
        Проверяет, что метод `create_save_file` корректно обрабатывает длинные UUID и формирует корректный путь.
        """
        long_uuid = 'a' * 32  # Имитация очень длинного UUID
        with patch('app.utils.uuid.uuid4', return_value=long_uuid):
            path, filename = Utils.create_save_file(mock_upload_folder)

            assert len(filename) > len('результат_.xlsx')
            assert path.endswith(filename)



class TestExcelUtils:
    """
    Тесты для статического метода `check_excel_structure` класса `ExcelUtils`.
    """

    @pytest.fixture
    def valid_file_path(self, tmpdir):
        """Фикстура, создающая временный Excel-файл с корректной структурой."""
        df = pd.DataFrame({
            "Имя": ["Анна", "Иван"],
            "Возраст": [25, 30],
            "Город": ["Москва", "Санкт-Петербург"]
        })
        file_path = tmpdir.join("valid.xlsx")
        df.to_excel(file_path, index=False)
        return str(file_path)

    @pytest.fixture
    def invalid_file_path(self, tmpdir):
        """Фикстура, создающая временный Excel-файл с отсутствующими колонками."""
        df = pd.DataFrame({
            "Имя": ["Анна", "Иван"],
            "Город": ["Москва", "Санкт-Петербург"]
        })
        file_path = tmpdir.join("invalid.xlsx")
        df.to_excel(file_path, index=False)
        return str(file_path)

    @pytest.fixture
    def non_existent_file(self, tmpdir):
        """Путь к несуществующему файлу."""
        return str(tmpdir.join("nonexistent.xlsx"))

    def test_check_excel_structure_valid_columns(self, valid_file_path):
        """
        Проверяет успешное выполнение метода при наличии всех необходимых колонок.
        """
        columns = ["Имя", "Возраст", "Город"]
        result = ExcelUtils.check_excel_structure(valid_file_path, columns)
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == set(["Имя", "Возраст", "Город"])

    def test_check_excel_structure_missing_columns(self, invalid_file_path):
        """
        Проверяет, что метод генерирует исключение `ValueError`, если отсутствуют требуемые колонки.
        """
        columns = ["Имя", "Возраст", "Город"]
        with pytest.raises(ValueError) as exc_info:
            ExcelUtils.check_excel_structure(invalid_file_path, columns)
        assert "Не хватает колонок" in str(exc_info.value)

    def test_check_excel_structure_case_insensitive_comparison(self, valid_file_path):
        """
        Проверяет регистронезависимость сравнения названий колонок.
        """
        columns = ["имя", "возраст", "город"]
        result = ExcelUtils.check_excel_structure(valid_file_path, columns)
        assert isinstance(result, pd.DataFrame)

    def test_check_excel_structure_nonexistent_file(self, non_existent_file):
        """
        Проверяет, что метод генерирует исключение `ValueError`, если файл не существует.
        """
        columns = ["Имя", "Возраст", "Город"]
        with pytest.raises(ValueError) as exc_info:
            ExcelUtils.check_excel_structure(non_existent_file, columns)
        assert "Ошибка при чтении файла" in str(exc_info.value)

    def test_check_excel_structure_invalid_file_content(self, tmpdir):
        """
        Проверяет, что метод корректно обрабатывает ошибку чтения Excel-файла.
        """
        file_path = tmpdir.join("invalid_format.xlsx")
        with open(file_path, "w") as f:
            f.write("Это не Excel файл")  # Некорректный формат
        columns = ["Имя", "Возраст"]
        with pytest.raises(ValueError) as exc_info:
            ExcelUtils.check_excel_structure(str(file_path), columns)
        assert "Ошибка при чтении файла" in str(exc_info.value)

    def test_check_excel_structure_empty_columns_list(self, valid_file_path):
        """
        Проверяет, что метод возвращает DataFrame без ошибок, если список ожидаемых колонок пуст.
        """
        columns = []
        result = ExcelUtils.check_excel_structure(valid_file_path, columns)
        assert isinstance(result, pd.DataFrame)

    def test_check_excel_structure_extra_columns_ignored(self, valid_file_path):
        """
        Проверяет, что метод игнорирует дополнительные колонки в файле и не требует их.
        """
        columns = ["Имя", "Город"]
        result = ExcelUtils.check_excel_structure(valid_file_path, columns)
        assert isinstance(result, pd.DataFrame)
