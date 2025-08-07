import pandas as pd

class ExcelUtils:
    
    @staticmethod
    def checkfile(path: str, required_cols: list[str]) -> bool:
        """
        Проверяет наличие необходимых колонок в файле
        
        Args:
            path: Путь к файлу для проверки
            required_cols: Список обязательных колонок
            
        Returns:
            bool: True если все колонки присутствуют, False если нет
            
        Raises:
            FileNotFoundError: Если файл не существует
            ValueError: Если файл не может быть прочитан как Excel
        """
        try:
            # Читаем только заголовки для проверки колонок
            df = pd.read_excel(path, nrows=0)
            
            # Проверяем наличие всех требуемых колонок
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"Отсутствуют обязательные колонки: {', '.join(missing_cols)}")
                return False
                
            return True
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл не найден: {path}")
        except Exception as e:
            raise ValueError(f"Ошибка при чтении файла: {str(e)}")
        
    @staticmethod
    def prog_name_from_bitrix(row):
        if row['Описание'] is str and row['Описание'][:2] == 'ПЭ':
            name = row['Описание'][4:].split('; ')
        else:
            name = row['Название'][4:].split('; ')
        return name