from abc import ABC, abstractmethod

class AbstractLoader(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def load_programs(self):
        pass

    @abstractmethod
    def load_tractors(self):
        pass

    @abstractmethod
    def load_departments(self):
        pass

    @abstractmethod
    def create_reports(self):
        pass