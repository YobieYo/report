from abc import ABC, abstractmethod
from .schemas import ErrorSchema, SuccesSchema
import pandas as pd
import json
from .utils import Utils, DataFrameUtils, ExcelUtils
import os
from typing import Dict, List, Any
class Drawer(ABC):
    """
    Абстрактный класс для генерации отчётов.

    Предназначен для использования в наследуемых классах, которые реализуют логику создания и сохранения отчёта.
    """

    @abstractmethod
    def draw_report(self) -> SuccesSchema:
        """
        Абстрактный метод для генерации отчёта.

        Должен быть реализован в подклассе. Метод выполняет логику построения отчёта и возвращает
        объект `SuccesSchema`, содержащий сообщение об успешном выполнении и ссылку на скачивание файла.

        :return: Объект с результатом выполнения операции.
        :rtype: SuccesSchema
        """
        pass

class MergeDrawer(Drawer):
    """
    Класс для объединения и форматирования данных из двух Excel-файлов.

    Наследуется от абстрактного класса `Drawer` и реализует метод `draw_report`,
    который объединяет данные из веб-системы и Битрикс, переформатирует их,
    создаёт Excel-отчёт с несколькими листами (отчёты по бюро, статистика),
    добавляет цветовую индикацию для разных програм и сохраняет результат.
    """

    def __init__(
        self,
        web_df: pd.DataFrame,
        bitrix_df: pd.DataFrame,
        config: dict | None = None,
        config_path: str = r'app/report_config.json',
    ):
        """
        Инициализация объекта MergeDrawer.

        :param web_df: DataFrame с данными из веб-системы.
        :param bitrix_df: DataFrame с данными из Битрикс.
        :param config: Конфигурационный словарь. Если не указан — загружается из файла.
        :param config_path: Путь к JSON-файлу с конфигурацией (по умолчанию 'app/report_config.json').
        """
        self.web_df = web_df
        self.bitrix_df = bitrix_df

        if config is not None:
            self.config = config
        else:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = json.load(file)

    def _merge_content(self) -> pd.DataFrame:
        """
        Объединяет два DataFrame по ключевым колонкам.

        Выполняет следующие шаги:
        1. Оставляет только нужные колонки, указанные в конфиге.
        2. Нормализует данные: обрезает строки, заполняет пропуски.
        3. Объединяет таблицы по полям 'Название' и 'Опытный узел'.
        4. Удаляет дублирующиеся колонки, если они есть.
        5. Заполняет оставшиеся пропуски.

        :return: Объединённый DataFrame.
        """
        # Загружаемнужные колонки из битркса
        bitrix_cols = self.config['bitrix_columns']
        self.bitrix_df = self.bitrix_df.loc[:, bitrix_cols]

        # Длинные программы не вмещаются в названия задач на битркс
        # Их названия записывают в описание задачи
        # Описания начинающиеся с "ПЭ: " ставим в названия
        self.bitrix_df[['Название', 'Описание']] = self.bitrix_df.apply(
            lambda row: (row['Описание'], row['Название']) 
            if str(row['Описание']).startswith('ПЭ: ') 
            else (row['Название'], row['Описание']),
            axis=1,
            result_type='expand'
        )
        """self.bitrix_df = (
            self.bitrix_df
            .assign(Описание=self.bitrix_df['Описание'].str.split('; '))
            .explode('Описание')
        )

        self.bitrix_df = (
            self.bitrix_df
            .assign(Название=self.bitrix_df['Название'].str.split('; '))
            .explode('Название')
        )"""

        # Нормализация
        self.bitrix_df['Название'] = self.bitrix_df['Название'].apply(
            lambda x: x[4:] if str(x).startswith('ПЭ: ') else x
        )
        
        # Разделяем задачи по бюро
        self.bitrix_df = (
            self.bitrix_df
            .assign(Теги=self.bitrix_df['Теги'].str.split(', '))
            .explode('Теги')
        )

         #Разбиваем составные названия программ по "; " (как в веб-системе)
        self.bitrix_df['Название'] = self.bitrix_df['Название'].fillna('')  # Защита от NaN
        self.bitrix_df = (
            self.bitrix_df
            .assign(Название=self.bitrix_df['Название'].str.split(r'\s*;\s*'))  # Устойчиво к пробелам
            .explode('Название')
        )
        # Удаляем пустые и "только пробелы" после разбивки
        self.bitrix_df = self.bitrix_df[
            self.bitrix_df['Название'].notna() & 
            (self.bitrix_df['Название'].str.strip() != '')
        ].copy()
        self.bitrix_df['Название'] = self.bitrix_df['Название'].str.strip()

        web_cols = self.config['web_columns']
        self.web_df = self.web_df.loc[:, web_cols]
        self.web_df["ПЭ: Комментарий"] = self.web_df["ПЭ: Комментарий"].fillna(
            value='-'
        )
        
        self.web_df = (
            self.web_df
            .assign(**{'Опытный узел': self.web_df['Опытный узел'].str.split('; ')})
            .explode('Опытный узел')
        )
        
        
        self.web_df[['№ трактора', 'Опытный узел']] = self.web_df[['№ трактора', 'Опытный узел']].ffill()

        # Объединяем битрикс и веб по полям 'Название' и 'Опытный узел'
        result_df = pd.merge(
            self.bitrix_df,
            self.web_df,
            left_on='Название',
            right_on='Опытный узел',
            #how='right',
            how='left',
            suffixes=('_bitrix', '')  # правый без суффикса
        )
        

        result_df = result_df.ffill().bfill() 

        return result_df

    def _format_excel_report(self, group_col_name: str, output_file: str) -> None:
            """
            Форматирует и сохраняет данные в Excel-файл с несколькими листами.

            :param group_col_name: Название столбца для группировки (например, 'Бюро').
            :param output_file: Путь к выходному Excel-файлу.
            """
            grouped = self.result_df.groupby(group_col_name)

            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:

                # Создаем лист статистики
                self._create_stats_sheet(writer)
                self._create_conflict_sheet(writer)

                # Создаем листы по бюро
                for name, group in grouped:
                    sheet_name = str(name).replace(':', '').replace('\\', '').replace('/', '')[:31]
                    format_dict = {}

                    # рассчитываем статистику в шапке
                    name_counts = (
                        group.groupby('Опытный узел')['№ трактора']
                        .nunique()
                        .reset_index()
                        .rename(columns={'№ трактора': 'Количество тракторов'})
                    )

                    # Рассчитываем среднюю наработку для каждого опытного узла
                    avg_hours = (
                        group.groupby('Опытный узел')
                        .apply(lambda x: x.groupby('№ трактора')['Наработка, м/ч'].max().mean())
                        .reset_index(name='Средняя наработка, м/ч')
                        .round(1)
                    )

                    # Рассчитываем максимальную наработку для каждого опытного узла
                    max_hours = (
                        group.groupby('Опытный узел')['Продолжительность контроля, м/ч']
                        .agg(lambda x: x.unique()[0])  # берем единственное уникальное значение
                        .str.extract('(\d+)')[0]      # извлекаем число из строки (например, '2000 м/ч' → 2000)
                        .astype(float)                # преобразуем в число
                        .reset_index(name='Продолжительность контроля, м/ч')
                    )

                    # Объединяем данные
                    stats_df = pd.merge(name_counts, avg_hours, on='Опытный узел')
                    stats_df = pd.merge(stats_df, max_hours, on='Опытный узел')

                    # Вычисляем отношение средней к максимальной наработке
                    stats_df['Отношение avr/max'] = (stats_df['Средняя наработка, м/ч'] / stats_df['Продолжительность контроля, м/ч']).round(2) * 100

                    # Шапка страницы
                    header_df = pd.DataFrame({
                        'Опытный узел': stats_df['Опытный узел'],
                        'Пусто1': '',
                        'Пусто2': '',
                        'Пусто3': '',
                        'Пусто4': '',
                        'Количество тракторов': stats_df['Количество тракторов'],
                        'Средняя наработка, м/ч': stats_df['Средняя наработка, м/ч'],
                        'Отношение avr/max': stats_df['Отношение avr/max']
                    })

                    # Записываем шапку в Excel
                    header_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
                    worksheet = writer.sheets[sheet_name]

                    # Форматируем шапку
                    for row_offset, value in enumerate(header_df['Опытный узел'], start=1):
                        color = ExcelUtils.get_cell_color(value)
                        if color not in format_dict:
                            format_dict[color] = writer.book.add_format({
                                'bg_color': color, 
                                'valign': 'vcenter',
                                'border': 1,
                                })
                        worksheet.merge_range(
                            first_row=0 + row_offset,
                            first_col=0,
                            last_row=0 + row_offset,
                            last_col=4,
                            data=value,
                            cell_format=format_dict[color],
                        )

                    # Создаем формат заголовков
                    header_format = writer.book.add_format({
                        'bold': True,
                        'align': 'center',
                        'valign': 'vcenter',
                        'border': 1,
                        'text_wrap': True,
                    })

                    # Создаем заголовок шапки страницы
                    worksheet.merge_range(0, 0, 0, 4, 'Программа ПЭ:', header_format)
                    worksheet.write(0, 5, 'Количество тракторов', header_format)
                    worksheet.write(0, 6, 'Средняя наработка, м/ч', header_format)
                    worksheet.write(0, 7, 'Прогресс программы, %', header_format)

                    # Процентный формат (85% вместо 0.85)
                    percent_format = writer.book.add_format({"num_format": "0%"})
                    worksheet.set_column("H:H", None, percent_format)

                    num_of_programs = group.groupby('Опытный узел').size().shape[0]

                    # Добавляем прогресс-бары (data bars)
                    worksheet.conditional_format(
                        f"H2:H{num_of_programs+1}",  # Диапазон 
                        {
                            "type": "data_bar",
                            "bar_color": "#63C384",  # Зеленый
                            "bar_solid": True,       # Сплошная заливка (не градиент)
                            "min_type": "num",
                            "min_value": 0,          # Минимум для шкалы (0%)
                            "max_type": "num",
                            "max_value": 100,          # Максимум для шкалы (100%)
                        },
                    )



                    # Задаем размеры колонкам
                    start_row = len(name_counts) + 4
                    worksheet.set_column('A:A', 16)
                    worksheet.set_column('B:B', 20)
                    worksheet.set_column('C:C', 56)
                    worksheet.set_column('D:D', 18)
                    worksheet.set_column('E:E', 24)
                    worksheet.set_column('F:F', 12)
                    worksheet.set_column('G:G', 20)
                    worksheet.set_column('H:H', 104)
                    worksheet.set_column('I:I', 18)

                    # Убираем колонку бюро из таблицы
                    group = group.drop(columns=['Бюро'])
                    
                    # Заполняем заголовок главной таблицы
                    for i, col in enumerate(group.columns):
                        worksheet.write(
                            start_row-1,
                            i,
                            col,
                            header_format,
                        )
                    
                    # Записываем главную таблицу
                    group.to_excel(
                        writer,
                        sheet_name=sheet_name,
                        index=False,
                        startrow=start_row,
                        header=False,
                        )

                    # Задаем какую колонку раскрашиваем
                    colored_col = self.config["report_column_map"]["Опытный узел"][0]


                    # Раскрашиваем ячейки
                    for row_offset, value in enumerate(group['Опытный узел'], 0):
                        color = ExcelUtils.get_cell_color(value)
                        if color not in format_dict:
                            format_dict[color] = writer.book.add_format({
                                'bg_color': color,
                                'valign': 'vcenter',
                                'border': 1,
                                'text_wrap': True
                                })
                        worksheet.write(start_row + row_offset, colored_col, value, format_dict[color])

                    # Задаем форматирование для всех строк
                    cell_format = writer.book.add_format({
                        'text_wrap': True,
                        'valign': 'vcenter',
                        'border': 1,
                    })

                    for i in range(start_row, group.shape[0]+start_row):
                        worksheet.set_row(
                            i,
                            None,
                            cell_format,
                        )
    def _create_stats_sheet(self, writer):
        # Общая статистика
        total_tractors = pd.DataFrame(self.web_df.agg(
                func={
                    '№ трактора': 'nunique'
                },
            )).T.reset_index(drop=True)
        total_tractors = total_tractors.rename(columns={
                '№ трактора': 'Число тракторов'
            })
        
        total_programs = pd.DataFrame(self.bitrix_df.agg(
            func={
                'Название': 'nunique',
            }
        )).T.reset_index(drop=True)

        total = pd.concat([total_tractors, total_programs], axis=1)
        
        # Записываем общую статистику в Excel
        total.to_excel(
                excel_writer=writer,
                sheet_name='Статистика',
                index=False
            )

        # Статистика по бюро
        result = self.result_df.groupby('Бюро').agg({
                'Опытный узел': 'nunique',
                '№ трактора': 'nunique'
            }).reset_index()
        result = result.rename(columns={
                'Опытный узел': 'Число опытных узлов',
                '№ трактора': 'Число тракторов'
            })

        # Write bureau stats table below the total stats
        result.to_excel(
                excel_writer=writer,
                sheet_name='Статистика',
                index=False,
                startrow=len(total) + 2,
            )

        # Set column widths
        writer.sheets['Статистика'].set_column('A:A', 56)
        writer.sheets['Статистика'].set_column('B:B', 24)
        writer.sheets['Статистика'].set_column('C:C', 24)

        # Create a pie chart
        workbook = writer.book
        worksheet = writer.sheets['Статистика']
        
        # Create chart object
        chart = workbook.add_chart({'type': 'pie'})
        
        # Get the data range for the chart
        data_start_row = len(total) + 3  # +2 for startrow, +1 for header
        data_end_row = data_start_row + len(result) - 1
        
        # Наполняем круговую диаграмму
        chart.add_series({
            'categories': ['Статистика', data_start_row, 0, data_end_row, 0],
            'values': ['Статистика', data_start_row, 1, data_end_row, 1],
            'data_labels': {'percentage': True, 'category': True},
        })

        # Вставляем диаграмму в Excel
        worksheet.insert_chart(
            0,
            3, 
            chart,
            {
                'x_scale': 1.5,     # Масштаб по ширине (1.5x default)
                'y_scale': 2      # масштаб по высоте (1.5x default)
            })


    def _create_conflict_sheet(self, writer):
        merged = pd.merge(
            self.result_df, 
            self.bitrix_df,
            left_on='Опытный узел', 
            right_on='Название',
            how='outer',
            indicator=True
        )

        # Фильтруем только уникальные значения (только в одной таблице)
        df3 = merged[merged['_merge'] != 'both'].drop('_merge', axis=1).dropna(axis=1)
        
        df3.to_excel(
            excel_writer=writer,
            sheet_name='Конфликты',
            index=False,
        )

        sheet = writer.sheets['Конфликты']
        sheet.set_column('A:A', 54)
        sheet.set_column('B:B', 12)
        sheet.set_column('C:C', 54)


    def draw_report(self) -> SuccesSchema:
        """
        Основной метод для генерации отчёта.

        Последовательность действий:
        1. Объединение данных из двух источников.
        2. Переформатирование DataFrame согласно конфигурации.
        3. Сохранение результата в файл.
        4. Форматирование Excel-файла.
        5. Возврат успешного ответа с ссылкой на скачивание.

        :return: Объект `SuccesSchema`, содержащий сообщение и ссылку на скачивание файла.
        """
        # Сливаем 2 таблицы в одну
        self.result_df = self._merge_content()

        # Переименовываем и переставляем колонки
        col_map = self.config['report_column_map']
        self.result_df = DataFrameUtils.reformat_dataframe(
            df=self.result_df,
            column_map=col_map,
        )

        # Сохраняем отчет
        upload_folder = os.environ.get('UPLOAD_FOLDER')
        output_file, link_file = Utils.create_save_file(
            upl_folder=upload_folder,
        )

        # Форматируем Excel
        self._format_excel_report(
            group_col_name='Бюро',
            output_file=output_file,
        )

        return SuccesSchema(
            message='Отчет создан',
            download_link=link_file,
        )


class FormatDrawer(Drawer):
    """
    Класс для форматирования Excel-отчетов.

    Наследуется от базового класса `Drawer`. Использует конфигурацию из файла или переданную вручную,
    переформатирует данные, применяет стиль оформления к Excel-файлу и возвращает ссылку на скачивание.
    """

    def __init__(
        self,
        format_df: pd.DataFrame,
        config: dict | None = None,
        config_path: str = r'app/report_config.json',
    ):
        """
        Инициализация экземпляра класса.

        :param format_df: Исходный DataFrame с данными для форматирования.
        :type format_df: pd.DataFrame
        :param config: Необязательный параметр — пользовательская конфигурация. Если не задан,
                       загружается из указанного файла.
        :type config: dict | None
        :param config_path: Путь к файлу конфигурации (по умолчанию 'app/report_config.json').
        :type config_path: str
        """
        self.format_df = format_df

        if config is not None:
            self.config = config
        else:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = json.load(file)

    def _format_excel_report(self, output_file: str, sheet_name: str):
        """
        Внутренний метод для форматирования Excel-файла.

        Применяет стили к колонкам и строкам, задает ширину столбцов и центрирование текста.

        :param output_file: Путь к файлу, в который будет сохранён Excel-отчёт.
        :type output_file: str
        :param sheet_name: Название листа Excel.
        :type sheet_name: str
        """
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:

            result_df = self.result_df.ffill()

            result_df.to_excel(
                excel_writer=writer,
                sheet_name=sheet_name,
                index=False,
            )

            worksheet = writer.sheets[sheet_name]
            worksheet.set_column('A:A', 16)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 16)
            worksheet.set_column('D:D', 16)
            worksheet.set_column('E:E', 24)
            worksheet.set_column('F:F', 56)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 104)
            worksheet.set_column('I:I', 24)
            worksheet.set_column('J:J', 24)

            # Задаем форматирование для всех строк
            cell_format = writer.book.add_format({
                'text_wrap': True,
                'valign': 'vcenter',
                'border': 1,
                'align': 'center',
            })

            # Применяем форматирование ко всем строкам
            for i in range(1, self.format_df.shape[0]):
                worksheet.set_row(
                    i,
                    None,
                    cell_format,
                )

    def draw_report(self):
        """
        Основной метод для генерации и сохранения отчета.

        Выполняет следующие шаги:
        1. Переформатирует исходные данные согласно `config['format_column_map']`.
        2. Сохраняет результат в файл.
        3. Применяет форматирование к Excel.
        4. Возвращает объект `SuccesSchema` с сообщением об успехе и ссылкой на скачивание.

        :return: Объект `SuccesSchema`, содержащий сообщение и ссылку на скачивание.
        :rtype: SuccesSchema
        """
        self.result_df = DataFrameUtils.reformat_dataframe(
            df=self.format_df,
            column_map=self.config['format_column_map'],
        )

        # Сохраняем отчет
        upload_folder = os.environ.get('UPLOAD_FOLDER')
        output_file, link_file = Utils.create_save_file(
            upl_folder=upload_folder,
        )

        # Форматируем Excel
        self._format_excel_report(
            output_file=output_file,
            sheet_name='Отчет'
        )

        return SuccesSchema(
            message='Отчет создан',
            download_link=link_file,
        )
