import os
from .schemas import SuccesSchema
from .utils import Utils, ExcelUtils
import json
from .drawer import MergeDrawer


class MergeController:
    """
    Контроллер для выполнения операции объединения данных из двух Excel-файлов.

    Обрабатывает загрузку файлов, проверяет структуру данных и передаёт данные в `MergeDrawer` для генерации отчёта.
    """

    @staticmethod
    def merge(web_file, bitrix_file) -> SuccesSchema:
        """
        Выполняет процесс объединения двух Excel-файлов.

        1. Сохраняет загруженные файлы в указанную папку.
        2. Проверяет наличие необходимых колонок в каждом файле.
        3. Передаёт обработанные данные в `MergeDrawer` для формирования результата.
        4. Возвращает объект `SuccesSchema` с сообщением и ссылкой на скачивание.

        :param web_file: Файл из веб-системы.
        :param bitrix_file: Файл из Битрикс.
        :return: Объект `SuccesSchema`, содержащий результат операции.
        :rtype: SuccesSchema
        :raises ValueError: Если произошла ошибка при чтении или проверке структуры файлов.
        """
        print('начинаем сливать')

        # Сохранение файлов
        upload_folder = os.environ.get('UPLOAD_FOLDER')
        web_path, bitrix_path = Utils.save_uploaded_files(
            files=[web_file, bitrix_file],
            upload_folder=upload_folder
        )

        # Проверяем правильность данных
        with open(r'app/report_config.json', encoding='utf-8') as f:
            config = json.load(f)
            web_columns = config["web_columns"]
            bitrix_columns = config["bitrix_columns"]

        web_df = ExcelUtils.check_excel_structure(
            file_path=web_path,
            columns=web_columns
        )
        bitrix_df = ExcelUtils.check_excel_structure(
            file_path=bitrix_path,
            columns=bitrix_columns
        )

        # Создаем отчет
        drawer = MergeDrawer(
            web_df=web_df,
            bitrix_df=bitrix_df
        )
        return drawer.draw_report()

        
    
class FormatController():
    pass

