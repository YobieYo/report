import os
import time
import datetime
import pytest
from unittest.mock import Mock, call, patch
from app import DataCleaner  


class TestDataCleaner:
    """
    Тесты для класса `DataCleaner`, отвечающего за автоматическую очистку старых файлов.
    """

    @pytest.fixture
    def data_cleaner(self):
        """Фикстура, создающая экземпляр `DataCleaner` для тестирования."""
        return DataCleaner(folders=['/mock/folder'], max_life_time=100)

    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.path.getmtime')
    @patch('os.remove')
    def test_delete_file_removes_old_files(
        self,
        mock_remove,
        mock_getmtime,
        mock_isfile,
        mock_listdir,
        data_cleaner
    ):
        """
        Проверяет, что `_delete_file` удаляет файл, если он старше заданного времени.
        """
        mock_isfile.return_value = True
        now = datetime.datetime.now()
        old_timestamp = (now - datetime.timedelta(seconds=200)).timestamp()
        mock_getmtime.return_value = old_timestamp

        data_cleaner._delete_file(now, '/mock/folder', 'old_file.txt')

        mock_remove.assert_called_once_with(os.path.join('/mock/folder', 'old_file.txt'))

    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.path.getmtime')
    @patch('os.remove')
    def test_delete_file_skips_new_files(
        self,
        mock_remove,
        mock_getmtime,
        mock_isfile,
        mock_listdir,
        data_cleaner
    ):
        """
        Проверяет, что `_delete_file` не удаляет файл, если он моложе заданного времени.
        """
        mock_isfile.return_value = True
        now = datetime.datetime.now()
        new_timestamp = (now - datetime.timedelta(seconds=50)).timestamp()
        mock_getmtime.return_value = new_timestamp

        data_cleaner._delete_file(now, '/mock/folder', 'new_file.txt')

        mock_remove.assert_not_called()

    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.path.getmtime')
    @patch('os.remove')
    def test_delete_file_handles_exception_silently(
        self,
        mock_remove,
        mock_getmtime,
        mock_isfile,
        mock_listdir,
        data_cleaner,
        capsys
    ):
        """
        Проверяет, что `_delete_file` обрабатывает исключения при удалении файла и печатает сообщение.
        """
        mock_isfile.return_value = True
        now = datetime.datetime.now()
        old_timestamp = (now - datetime.timedelta(seconds=200)).timestamp()
        mock_getmtime.return_value = old_timestamp
        mock_remove.side_effect = Exception("Permission denied")

        data_cleaner._delete_file(now, '/mock/folder', 'error_file.txt')

        captured = capsys.readouterr()
        assert "Не удалось удалить файл" in captured.out

    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.path.getmtime')
    def test_clean_folder_processes_all_files(
        self,
        mock_getmtime,
        mock_isfile,
        mock_listdir,
        data_cleaner
    ):
        """
        Проверяет, что `_clean_folder` вызывает `_delete_file` для каждого файла в папке.
        """
        mock_listdir.return_value = ['file1.txt', 'file2.txt']
        mock_isfile.return_value = True
        now = datetime.datetime.now()

        with patch.object(data_cleaner, '_delete_file') as mock_delete_file:
            data_cleaner._clean_folder(now, '/mock/folder')

            assert mock_delete_file.call_count == 2
            mock_delete_file.assert_any_call(now, '/mock/folder', 'file1.txt')
            mock_delete_file.assert_any_call(now, '/mock/folder', 'file2.txt')


    def test_constructor_prints_message(self, capsys):
        """
        Проверяет, что конструктор выводит сообщение при создании экземпляра `DataCleaner`.
        """
        DataCleaner(folders=['/test'], max_life_time=100)
        captured = capsys.readouterr()
        assert "Создан уборщик данных" in captured.out
