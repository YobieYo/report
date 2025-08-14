from abc import ABC, abstractmethod
from .schemas import ErrorSchema, SuccesSchema
import pandas as pd
import json
from .utils import Utils
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

    def _reformat_dataframe(self, df: pd.DataFrame, column_map: Dict[str, List[Any]]) -> pd.DataFrame:
        """
        Переформатирует DataFrame согласно заданному отображению колонок.

        :param df: Исходный DataFrame.
        :param column_map: Словарь с новыми названиями и порядком колонок.
        :return: Отформатированный DataFrame.
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

    def _format_excel_report(self, group_col_name: str, output_file: str) -> None:
        """
        Форматирует и сохраняет данные в Excel-файл с несколькими листами.

        :param group_col_name: Название столбца для группировки (например, 'Бюро').
        :param output_file: Путь к выходному Excel-файлу.
        """
        grouped = self.result_df.groupby(group_col_name)

        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:

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

            result = self.result_df.groupby('Бюро').agg({
                'Опытный узел': 'nunique',
                '№ трактора': 'nunique'
            }).reset_index()
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
                sheet_name = str(name).replace(':', '').replace('\\', '').replace('/', '')[:31]
                format_dict = {}

                name_counts = (
                    group.groupby('Опытный узел')['№ трактора']
                    .nunique()
                    .reset_index()
                    .rename(columns={'№ трактора': 'Количество тракторов'})
                )

                header_df = pd.DataFrame({
                    'Опытный узел': name_counts['Опытный узел'],
                    'Пусто1': '',
                    'Пусто2': '',
                    'Пусто3': '',
                    'Пусто4': '',
                    'Количество тракторов': name_counts['Количество тракторов']
                })

                header_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
                worksheet = writer.sheets[sheet_name]

                for row_offset, value in enumerate(header_df['Опытный узел'], start=1):
                    color = self._get_cell_color(value)
                    if color not in format_dict:
                        format_dict[color] = writer.book.add_format({'bg_color': color})
                    worksheet.merge_range(
                        first_row=0 + row_offset,
                        first_col=0,
                        last_row=0 + row_offset,
                        last_col=4,
                        data=value,
                        cell_format=format_dict[color],
                    )

                header_format = writer.book.add_format({
                    'bold': True,
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                    'text_wrap': True,
                })

                worksheet.merge_range(0, 0, 0, 4, 'Программа ПЭ:', header_format)
                worksheet.write(0, 5, 'Количество тракторов', header_format)

                start_row = len(name_counts) + 3
                worksheet.set_column('A:A', 16)
                worksheet.set_column('B:B', 20)
                worksheet.set_column('C:C', 56)
                worksheet.set_column('D:D', 18)
                worksheet.set_column('E:E', 24)
                worksheet.set_column('F:F', 12)
                worksheet.set_column('G:G', 20)
                worksheet.set_column('H:H', 104)
                worksheet.set_column('I:I', 18)

                group = group.drop(columns=['Бюро'])
                group.to_excel(writer, sheet_name=sheet_name, index=False, startrow=start_row)

                colored_col = self.config["report_column_map"]["Опытный узел"][0]

                for row_offset, value in enumerate(group['Опытный узел'], start=1):
                    color = self._get_cell_color(value)
                    if color not in format_dict:
                        format_dict[color] = writer.book.add_format({'bg_color': color})
                    worksheet.write(start_row + row_offset, colored_col, value, format_dict[color])

    def _get_cell_color(self, value: str) -> str:
        """
        Генерирует HEX-цвет на основе хеша строки.

        :param value: Входная строка.
        :return: HEX-код цвета.
        """
        hash_integer = abs(hash(str(value)))

        r = 150 + (hash_integer % 101) & 0xFF
        g = 150 + ((hash_integer // 100) % 101)
        b = 150 + ((hash_integer // 10000) % 101)

        r = min(r, 255)
        g = min(g, 255)
        b = min(b, 255)

        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        return hex_color

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
        self.result_df = self._reformat_dataframe(
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

    

