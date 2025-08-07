from abc import ABC, abstractmethod

class AbstractDrawer(ABC):

    @abstractmethod
    def draw(self):
        pass