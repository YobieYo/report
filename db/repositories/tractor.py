from ..models import Tractor
from .base import BaseRepository

class TractorRepository(BaseRepository[Tractor]):
    def __init__(self):
        super().__init__(Tractor)