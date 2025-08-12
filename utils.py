import uuid
import os
from typing import Tuple, List
import pandas as pd

class Utils:

    @staticmethod
    def save_uploaded_files(files : list, upload_folder : str) -> Tuple[str]:
        file_id = str(uuid.uuid4())
        file_paths = list()
        for file in files:
            unique_name =   f'{file_id}_{file.filename}'
            path = os.path.join(upload_folder, unique_name)
            file.save(path)
            file_paths.append(path)
        return tuple(file_paths)
    
    @staticmethod
    def create_save_file(upl_folder : str) -> str:
        file_id = str(uuid.uuid4())
        unique_name =   f'результат_{file_id}.xlsx'
        path = os.path.join(upl_folder, unique_name)

        return path, unique_name
    
class ExcelUtils:
    @staticmethod
    def check_excel_structure(file_path : str, columns : List[str]):
        try:
            df = pd.read_excel(file_path)
            actual_columns = set(col.strip().lower() for col in df.columns)
            required_set = set(col.strip().lower() for col in columns)
            
            if not required_set.issubset(actual_columns):
                missing = required_set - actual_columns
                raise ValueError(f"Не хватает колонок: {missing}")
            return df
        except Exception as e:
            raise ValueError(f"ошибка при чтении файла: {str(e)}")
        
