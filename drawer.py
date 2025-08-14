from abc import ABC, abstractmethod
from schemas import ErrorSchema, SuccesSchema
import pandas as pd
import json
from utils import Utils
import os


class drawer(ABC):

    @abstractmethod
    def draw_report(self) -> SuccesSchema:
        pass

class MergeDrawer(drawer):
    def __init__(
        self,
        web_df: pd.DataFrame,
        bitrix_df: pd.DataFrame,
        config: dict | None = None,
        config_path: str = 'report_config.json',
    ):
        self.web_df = web_df
        self.bitrix_df = bitrix_df

        if config is not None:
            self.config = config
        else:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = json.load(file)

    def _merge_content(self):
        bitrix_cols = self.config['bitrix_columns']
        self.bitrix_df = self.bitrix_df.loc[:, bitrix_cols]

        web_cols = self.config['web_columns']
        self.web_df = self.web_df.loc[:, web_cols]

        # нормализация
        self.bitrix_df['Название'] = self.bitrix_df['Название'].str[4:]
        self.web_df[['№ трактора', 'Опытный узел']] = self.web_df[['№ трактора', 'Опытный узел']].ffill()

        # берём «Бюро» из web (правый df), bitrix-поле — если нужно — уходит в _bitrix
        result_df = pd.merge(
            self.bitrix_df,
            self.web_df,
            left_on='Название',
            right_on='Опытный узел',
            how='right',
            suffixes=('_bitrix', '')  # правый без суффикса
        )

        result_df = result_df.ffill().bfill()

        # если из bitrix тоже пришло «Бюро», удалим его
        if 'Бюро_bitrix' in result_df.columns and 'Бюро' in result_df.columns:
            result_df = result_df.drop(columns=['Бюро_bitrix'])

        return result_df


    
    def _reformat_dataframe(self, df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
        """
        Переформатирует DataFrame согласно заданному отображению колонок,
        удаляя все столбцы, не указанные в column_map.
        
        Параметры:
        ----------
        df : pd.DataFrame
            Исходный DataFrame для переформатирования
        column_map : dict
            Словарь с отображением колонок в формате:
            {
                "новое_название": [индекс_колонки, "старое_название"],
                ...
            }
        
        Возвращает:
        -----------
        pd.DataFrame
            Новый DataFrame только с указанными колонками, переименованными и упорядоченными
        """
        # Создаем словарь для переименования и отбора колонок
        rename_dict = {}
        columns_to_keep = []
        
        for new_name, (index, old_name) in column_map.items():
            if old_name in df.columns:
                rename_dict[old_name] = new_name
                columns_to_keep.append(old_name)
        
        # Отбираем только нужные колонки и переименовываем их
        df_filtered = df[columns_to_keep].rename(columns=rename_dict)
        
        # Сортируем колонки согласно индексам из column_map
        new_columns_order = [k for k, _ in sorted(column_map.items(), key=lambda x: x[1][0])]
        
        # Возвращаем DataFrame только с нужными колонками в правильном порядке
        return df_filtered[new_columns_order]

    def _format_excel_report(self, group_col_name : str, output_file : str):

        
        # Группируем на листах по столбцу  (например, "Теги")
        grouped = self.result_df.groupby(group_col_name)
        
        
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:

            total = pd.DataFrame(self.result_df.agg(
                func = {
                'Опытный узел': 'nunique',
                '№ трактора': 'nunique'
                },
                )).T.reset_index(drop=True)
            total = total.rename(columns={
                    'Опытный узел': 'Число опытных узлов',
                    '№ трактора': 'Число тракторов'
            })
            total.to_excel(
                excel_writer=writer,
                sheet_name='Статистика',
                index=False
            )

            # Лист со статистикой
            result = self.result_df.groupby('Бюро').agg({
                'Опытный узел': 'nunique',
                '№ трактора': 'nunique'
            }).reset_index()

            # Переименуем столбцы для ясности
            result = result.rename(columns={
                'Опытный узел': 'Число опытных узлов',
                '№ трактора': 'Число тракторов'
            })

            result.to_excel(
                excel_writer=writer,
                sheet_name='Статистика',
                index=False,
                startrow=len(total) + 2,
            )

            writer.sheets['Статистика'].set_column('A:A', 56)
            writer.sheets['Статистика'].set_column('B:B', 24)
            writer.sheets['Статистика'].set_column('C:C', 24)



            for name, group in grouped:
                # Очищаем название листа (убираем запрещённые символы и обрезаем до 31 символа)
                sheet_name = str(name).replace(':', '').replace('\\', '').replace('/', '')[:31]

                format_dict = {}

                name_counts = (
                    group.groupby('Опытный узел')['№ трактора']  # Группируем по "Название" и берём "№ трактора"
                    .nunique()  # Считаем количество уникальных тракторов
                    .reset_index()  # Преобразуем в DataFrame
                    .rename(columns={'№ трактора': 'Количество тракторов'})
                )

                header_df = pd.DataFrame({
                    'Опытный узел': name_counts['Опытный узел'],  # Колонка A (индекс 0)
                    'Пусто1': '',                         # Колонка B (индекс 1)
                    'Пусто2': '',                         # Колонка C (индекс 2)
                    'Пусто3': '',                         # Колонка D (индекс 3)
                    'Пусто4': '',                         # Колонка E (индекс 4)
                    'Количество тракторов': name_counts['Количество тракторов']  # Колонка F (индекс 5)
                })


                # Записываем статистику
                header_df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                    startrow=0
                )

                # Получаем объект листа
                worksheet = writer.sheets[sheet_name]

                for row_offset, value in enumerate(header_df['Опытный узел'], start=1):
                    color = self._get_cell_color(value)
                    
                    if color not in format_dict:
                        format_dict[color] = writer.book.add_format({'bg_color': color})
                    
                    # Правильно рассчитываем номер строки
                    worksheet.merge_range(
                        first_row = 0 + row_offset,
                        first_col = 0,
                        last_row = 0 + row_offset,
                        last_col = 4,
                        data = value,
                        cell_format = format_dict[color],
                    )

                

                # Форматирование для статистики
                header_format = writer.book.add_format({
                    'bold': True,
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                    'text_wrap': True,
                })

                # Объединяем первые 5 ячеек для заголовка "Программа ПЭ:"
                worksheet.merge_range(0, 0, 0, 4, 'Программа ПЭ:', header_format)
                
                # Записываем заголовок "Количество тракторов" в 6-ю колонку
                worksheet.write(0, 5, 'Количество тракторов', header_format)
                 # Записываем основную таблицу с отступом
                start_row = len(name_counts) + 3  # Отступ от статистики

                # Устанавливаем ширину столбцов
                worksheet.set_column('A:A', 16)
                worksheet.set_column('B:B', 20, )
                worksheet.set_column('C:C', 56)
                worksheet.set_column('D:D', 18, )
                worksheet.set_column('E:E', 24, )
                worksheet.set_column('F:F', 12, )
                worksheet.set_column('G:G', 20, )
                worksheet.set_column('H:H', 104, )
                worksheet.set_column('I:I', 18, )

                group = group.drop(
                    columns=['Бюро']
                )

                group.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                    startrow=start_row,
                )
                
                colored_col = self.config["report_column_map"]["Опытный узел"][0]


                for row_offset, value in enumerate(group['Опытный узел'], start=1):
                    color = self._get_cell_color(value)
                    
                    if color not in format_dict:
                        format_dict[color] = writer.book.add_format({'bg_color': color})
                    
                    # Правильно рассчитываем номер строки
                    worksheet.write(start_row + row_offset, colored_col, value, format_dict[color])

    def _get_cell_color(self, value):
        """
        Преобразует строку в HEX-цвет (#RRGGBB) на основе её хеша.
        
        Параметры:
            value (str): Входная строка.
        
        Возвращает:
            str: HEX-код цвета, например "#a1b2c3".
        """
        # Вычисляем хеш строки и берём его абсолютное значение
        hash_integer = abs(hash(str(value)))

        
        # Используем первые 3 байта хеша для RGB
        r = 150 + (hash_integer % 101) & 0xFF  # Красный
        g = 150 + ((hash_integer // 100) % 101)   # Зелёный
        b = 150 + ((hash_integer // 10000) % 101) 
        
        # Корректируем, чтобы не выйти за 255
        r = min(r, 255)
        g = min(g, 255)
        b = min(b, 255)        # Синий
            
        # Форматируем в HEX (#RRGGBB)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        
        return hex_color


    def draw_report(self) -> SuccesSchema:

        # Сливаем 2 таблице в одну
        self.result_df = self._merge_content()

        # Переименовываем и переставляем колонки
        col_map = self.config['report_column_map']
        self.result_df = self._reformat_dataframe(
            df = self.result_df,
            column_map = col_map,
        )
        
        # Сохраняем отчет
        upload_folder = os.environ.get('UPLOAD_FOLDER')
        output_file, link_file = Utils.create_save_file(
            upl_folder=upload_folder,
        )
        
        # Форматируем Excel
        self._format_excel_report(
            group_col_name = 'Бюро',
            output_file=output_file,
        )

        print('Дошли до создания отчета')
        return SuccesSchema(
            message='Отчет создан',
            download_link=link_file,
        )
    

