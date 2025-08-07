from ..models import Department
from .base import BaseRepository
from db.database import db
from db.models import Program
from typing import List

class DepartmentRepository(BaseRepository[Department]):
    def __init__(self):
        super().__init__(Department)

    def get_programs_for_department(self, department_id: int) -> List[Program]:
        department = db.session.query(Department).get(department_id)
        
        if not department:
            return []
        
        programs = list()
        for program in department.programs:
            programs.append(program)
        return programs
