from ..abstract_loader import AbstractLoader
from db.repositories import report_repository, program_repository, tractor_repository, department_repository
import pandas as pd
from datetime import datetime, date
from .excel_utils import ExcelUtils

class ExcelLoader(AbstractLoader):
    def __init__(self, bitrix_path : str, web_path : str):
        self.bitrix_path = bitrix_path
        self.web_path = web_path

        self.df_web = pd.read_excel(self.web_path)
        self.df_bitrix = pd.read_excel(self.bitrix_path)

        ExcelUtils.checkfile(
            self.bitrix_path,
            [
                'Название',
                'Примечание',
                'Описание',
                'Теги',
            ]
        )
        ExcelUtils.checkfile(
            self.web_path,
            [
                'Модель трактора', 
                '№ трактора', 
                'Граничная дата гарантии', 
                'Опытный узел'
            ]
        )
    
    # --- Загружаем программы, только названия и продолжительность --- 
    def load_programs(self) -> None:
        """
            Загрузка программ из файла bitrix excel
        """
        df = self.df_bitrix.dropna(
            subset=[
                'Название',
                'Примечание',
            ]
        )

        for i, row in df.iterrows():
            name = ExcelUtils.prog_name_from_bitrix(row)

            duration = row['Примечание']
            for each in name:
                program_repository.create(name = str(each), observation_duration = duration)
        return None


    # --- Загружаем трактора и привязываем их к программам ---
    def load_tractors(self) -> None:
        """
            Загрузка тракторов из файла ВЕБ ГСО excel и их связи с программами
        """

        df = self.df_web.dropna(
            subset=['Модель трактора', '№ трактора', 'Граничная дата гарантии', 'Опытный узел'])
        for i, row in df.iterrows():
            model_name = row['Модель трактора']
            serial_number = row['№ трактора']
            warranty_expire_date = row['Граничная дата гарантии']

            tractor_id = tractor_repository.create(
                model_name = model_name,
                serial_number = serial_number,
                warranty_expire_date = warranty_expire_date
            ).id

            program_name = row['Опытный узел'].split('; ')

            for each in program_name:
                program = program_repository.get_by_name(each)
                
                
                if program is not None:
                    program_repository.add_tractor_to_program(
                        program_id = program.id,
                        tractor_id = tractor_id
                    )
                    if program.is_active == False:
                        program_repository.set_active(
                            program_id = program.id,
                        )

                
            
        return None

    def load_departments(self) -> None:
        """
        создание бюро из bitrix excel и привязка программ к ним
        """

        df = self.df_bitrix.dropna(
            subset=['Название', 'Теги', 'Описание']
        )

        for i, row in df.iterrows():
            departments = row['Теги'].split(', ')
            program_name = ExcelUtils.prog_name_from_bitrix(row)

            for name in program_name:
                program = program_repository.get_by_name(
                    name = name
                )

                if program is not None:
                    for department in departments:
                        department_id = department_repository.create(
                            name = department
                        ).id

                    program_repository.add_department_to_program(
                        program_id = program.id,
                        department_id = department_id
                )

    def create_reports(self):
        df = pd.read_excel(self.web_path)

        df = self.df_web.dropna(subset = ['ПЭ: Комментарий'])
        df[['№ трактора', 'Опытный узел', ]] = df[['№ трактора', 'Опытный узел']].copy().ffill()

        for i, row in df.iterrows():
            comment = row['ПЭ: Комментарий']
            tractor = tractor_repository.get_by_fields(
                serial_number = row['№ трактора']
            )
            if tractor is not None:
                tractor_id = tractor.id

            program = program_repository.get_by_name(
                name = row['Опытный узел']
            )

            if program is not None:
                program_id = program.id

            defect_detected_at_hours = str(row['ПЭ: наработка м/ч'])

            operating_hours = str(row['Наработка, м/ч'])

            report_time = str(row['ПЭ: дата время'])

            parameters = [comment, tractor_id, program_id, defect_detected_at_hours, operating_hours, report_time]

            if parameters is not None:
                report_repository.create(
                    comment=comment,
                    program_id=program_id,
                    tractor_id=tractor_id,
                    defect_detected_at_hours=defect_detected_at_hours,
                    operating_hours=operating_hours,
                    report_time=report_time
                )  