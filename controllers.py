import os
from schemas import MergeSchema, SuccesSchema, ErrorSchema
from utils import Utils, ExcelUtils
from abc import ABC, abstractmethod
import json
from drawer import MergeDrawer

class Controller(ABC):

    @abstractmethod
    def run(self) -> SuccesSchema:
        pass

class MergeController(Controller):

    @staticmethod
    def merge(web_file, bitrix_file) -> SuccesSchema:
        print('начинаем сливать')
        # Сохранение файлов
        upload_folder = os.environ.get('UPLOAD_FOLDER')
        web_path, bitrix_path = Utils.save_uploaded_files(
            files=[web_file, bitrix_file],
            upload_folder=upload_folder
        )
        print('данные сохранены')

        # Проверяем правильность данных
        with open('report_config.json', encoding='utf-8') as f:
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
        
        print('данные проверены, начинаем сливать')
        
        # Создаем отчет
        drawer = MergeDrawer(
            web_df=web_df,
            bitrix_df=bitrix_df
        )
        print('создан работник')
        return drawer.draw_report()
        
    




class FormatController:
    def run():
        pass


