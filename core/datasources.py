from abc import ABC, abstractmethod

class DataSource(ABC):
    @abstractmethod
    def load(self):
        """Retorna um DataFrame pandas"""
        pass
