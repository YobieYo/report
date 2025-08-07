from datetime import datetime
from ..models import Report, db
from .base import BaseRepository
from typing import List
from db.models import Report

class ReportRepository(BaseRepository[Report]):
    def __init__(self):
        super().__init__(Report)

    