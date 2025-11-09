from abc import ABC, abstractmethod
from typing import Any


class DataSource(ABC):
    @abstractmethod
    def load(self, config: object) -> None:
        pass
