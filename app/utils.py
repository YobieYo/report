import uuid
import os
from typing import Tuple, List
import pandas as pd

class Utils:
    """
    Вспомогательный класс для выполнения общих операций, связанных с обработкой файлов.

    Содержит статические методы для сохранения загруженных файлов и генерации уникальных имен для файлов.
    """

    @staticmethod
    def save_uploaded_files(files: List, upload_folder: str) -> Tuple[str]:
        """
        Сохраняет список загруженных файлов в указанную папку.

        Каждому файлу присваивается уникальное имя на основе UUID4. Сохранённые пути возвращаются в виде кортежа.

        :param files: Список объектов файлов, которые нужно сохранить.
        :type files: List
        :param upload_folder: Путь к папке, в которую будут сохранены файлы.
        :type upload_folder: str
        :return: Кортеж, содержащий пути к сохранённым файлам.
        :rtype: Tuple[str]
        """
        file_id = str(uuid.uuid4())
        file_paths = list()
        for file in files:
            unique_name = f'{file_id}_{file.filename}'
            path = os.path.join(upload_folder, unique_name)
            file.save(path)
            file_paths.append(path)
        return tuple(file_paths)

    @staticmethod
    def create_save_file(upl_folder: str) -> str:
        """
        Генерирует уникальное имя и полный путь для нового файла результата.

        Имя файла формируется по шаблону 'результат_{uuid}.xlsx', где {uuid} — это случайный идентификатор.

        :param upl_folder: Путь к папке, в которую будет сохранён файл.
        :type upl_folder: str
        :return: Полный путь и имя файла.
        :rtype: str
        """
        file_id = str(uuid.uuid4())
        unique_name = f'результат_{file_id}.xlsx'
        path = os.path.join(upl_folder, unique_name)
        return path, unique_name

class ExcelUtils:
    """
    Вспомогательный класс для работы с Excel-файлами.

    Содержит статические методы для проверки структуры данных в Excel-файлах.
    """

    @staticmethod
    def check_excel_structure(file_path: str, columns: List[str]):
        """
        Проверяет, содержит ли Excel-файл указанные колонки.

        Метод считывает файл и сравнивает набор требуемых колонок с теми, что присутствуют в файле.
        Если какие-либо из требуемых колонок отсутствуют, генерируется исключение `ValueError`.

        :param file_path: Путь к Excel-файлу.
        :type file_path: str
        :param columns: Список ожидаемых колонок (регистр не важен).
        :type columns: List[str]
        :return: DataFrame, считанный из файла.
        :rtype: pandas.DataFrame
        :raises ValueError: Если файл содержит недостающие колонки или произошла ошибка чтения.
        """
        try:
            df = pd.read_excel(file_path)
            actual_columns = set(col.strip().lower() for col in df.columns)
            required_set = set(col.strip().lower() for col in columns)

            if not required_set.issubset(actual_columns):
                missing = required_set - actual_columns
                raise ValueError(f"Не хватает колонок: {missing}")
            return df
        except Exception as e:
            raise ValueError(f"Ошибка при чтении файла: {str(e)}")

        
