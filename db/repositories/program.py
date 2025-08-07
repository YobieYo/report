from ..models import Program, db, Report
from .base import BaseRepository
from typing import List

class ProgramRepository(BaseRepository[Program]):
    def __init__(self):
        super().__init__(Program)

    def add_tractor_to_program(self, program_id: int, tractor_id: int) -> Program:
        program = self.get_by_id(program_id)
        if program:
            from .tractor import TractorRepository
            tractor = TractorRepository().get_by_id(tractor_id)
            if tractor:
                program.tractors.append(tractor)
                db.session.commit()
        return program

    def add_department_to_program(self, program_id: int, department_id: int) -> Program:
        program = self.get_by_id(program_id)
        if program:
            from .department import DepartmentRepository
            department = DepartmentRepository().get_by_id(department_id)
            if department:
                program.departments.append(department)
                db.session.commit()
        return program
    
    def get_by_name(self, name: str) -> Program:
        """Find a program by its name.
        
        Args:
            name: The name of the program to search for.
            
        Returns:
            The Program object if found, None otherwise.
        """
        return Program.query.filter_by(name=name).first()
    
    def get_active_programs(self) -> list[Program]:
        return Program.query.filter_by(is_active=True).all()
    
    def set_active(self, program_id):
        program = Program.query.filter_by(id=program_id).first()
        if program:
            if program.is_active == False:
                program.is_active = True
                db.session.commit()
        return program
    
    def get_reports(self, program_id) -> List[Report]:
        program = Program.query.filter_by(id=program_id).first()

        if program:
            if program.reports:
                return program.reports      
        else:
            return []


