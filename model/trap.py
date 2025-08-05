from abc import ABC, abstractmethod

class Trap(ABC):
    @abstractmethod
    def get_protocol(self) -> str:
        pass

    @abstractmethod
    def get_type(self) -> str:
        pass

    @abstractmethod
    def simulate_interaction(self, input_data: str, ip: str) -> None:
        pass