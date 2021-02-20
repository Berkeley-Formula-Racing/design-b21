from abc import ABC, abstractmethod

# TODO: refine
class Connection(ABC):
    @abstractmethod
    def get_available_devices(self):
        pass

    @abstractmethod
    def open(self, device): # address
        pass
    
    @abstractmethod
    def write(self, data):
        pass

    @abstractmethod()
    def read(self):
        pass
