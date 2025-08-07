from datetime import datetime
from ..models import Report, db
from .base import BaseRepository
from typing import List
from db.models import Report

class ReportRepository(BaseRepository[Report]):
    def __init__(self):
        super().__init__(Report)

    def create_report(self, program_id: int, tractor_id: int, comment: str, 
                     report_operating_hours: float, operating_hours: float) -> Report:
        report = self.create(
            program_id=program_id,
            tractor_id=tractor_id,
            comment=comment,
            report_operating_hours=report_operating_hours,
            operating_hours=operating_hours,
            report_time=datetime.utcnow()
        )
        return report

    def get_reports_for_department(self, department_id: int) -> List[Report]:
        from .department import DepartmentRepository
        department = DepartmentRepository().get_by_id(department_id)
        if not department:
            return []

        reports = []
        for program in department.programs:
            for tractor in program.tractors:
                reports.append(tractor.reports)
        return reports
    
    