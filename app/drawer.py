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
        bitrix_cols = self.config['bitrix_columns']
        self.bitrix_df = self.bitrix_df.loc[:, bitrix_cols]

        web_cols = self.config['web_columns']
        self.web_df = self.web_df.loc[:, web_cols]

        # нормализация
        self.bitrix_df['Название'] = self.bitrix_df['Название'].str[4:]
        self.web_df[['№ трактора', 'Опытный узел']] = self.web_df[['№ трактора', 'Опытный узел']].ffill()

        # Объединяем битрикс и веб по полям 'Название' и 'Опытный узел'
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

            # Создаем листы по бюро
            for name, group in grouped:
                sheet_name = str(name).replace(':', '').replace('\\', '').replace('/', '')[:31]
                format_dict = {}

                # расчитываем статистику в шапке
                name_counts = (
                    group.groupby('Опытный узел')['№ трактора']
                    .nunique()
                    .reset_index()
                    .rename(columns={'№ трактора': 'Количество тракторов'})
                )

                # Шапка страницы
                header_df = pd.DataFrame({
                    'Опытный узел': name_counts['Опытный узел'],
                    'Пусто1': '',
                    'Пусто2': '',
                    'Пусто3': '',
                    'Пусто4': '',
                    'Количество тракторов': name_counts['Количество тракторов']
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

                # Применяем форматирование ко всем строкам
                print(f'Начальная строка форматирвоание{start_row}')
                print(f'всего строк для форматирвания {group.shape[0]}')
                for i in range(start_row, group.shape[0]):
                    worksheet.set_row(
                        i,
                        None,
                        cell_format,
                    )

    def _create_stats_sheet(self, writer):
        # Create the total stats table
        total = pd.DataFrame(self.result_df.agg(
                func={
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

        # Create the bureau stats table
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
