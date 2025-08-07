from datetime import datetime
from .database import db

# Association table for many-to-many between Program and Tractor
program_tractor_association = db.Table(
    'program_tractor_association',
    db.Column('program_id', db.Integer, db.ForeignKey('programs.id')),
    db.Column('tractor_id', db.Integer, db.ForeignKey('tractors.id'))
)

# Association table for many-to-many between Program and Department
program_department_association = db.Table(
    'program_department_association',
    db.Column('program_id', db.Integer, db.ForeignKey('programs.id')),
    db.Column('department_id', db.Integer, db.ForeignKey('departments.id'))
)

class Program(db.Model):
    __tablename__ = "programs"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, unique=True, index=True)
    observation_duration = db.Column(db.String)
    is_active = db.Column(db.Boolean, default=False, index=True)
    
    tractors = db.relationship(
        "Tractor", 
        secondary=program_tractor_association,
        back_populates="programs"
    )
    
    departments = db.relationship(
        "Department",
        secondary=program_department_association,
        back_populates="programs"
    )
    
    # Change to one-to-many (a program can have multiple reports)
    reports = db.relationship("Report", back_populates="program", cascade="all, delete-orphan")

class Tractor(db.Model):
    __tablename__ = "tractors"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    model_name = db.Column(db.String)
    serial_number = db.Column(db.String, unique=True, index=True)
    warranty_expire_date = db.Column(db.String)
    
    # Many-to-many with Program
    programs = db.relationship(
        "Program",
        secondary=program_tractor_association,
        back_populates="tractors"
    )
    
    # One-to-many with Report
    reports = db.relationship("Report", back_populates="tractor", cascade="all, delete-orphan")

class Department(db.Model):
    __tablename__ = "departments"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, unique=True, index=True)
    
    # Many-to-many with Program
    programs = db.relationship(
        "Program",
        secondary=program_department_association,
        back_populates="departments"
    )

class Report(db.Model):
    __tablename__ = "reports"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    comment = db.Column(db.String)
    
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"))
    program = db.relationship("Program", back_populates="reports")
    
    tractor_id = db.Column(db.Integer, db.ForeignKey("tractors.id"))
    tractor = db.relationship("Tractor", back_populates="reports")
    
    defect_detected_at_hours = db.Column(db.String)
    operating_hours = db.Column(db.String)
    report_time = db.Column(db.String)