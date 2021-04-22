from abc import ABC, abstractmethod

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

    @abstractmethod
    def read(self, keep_reading):
        pass

    @abstractmethod
    def is_open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def flushInput(self):
        pass
    
    @abstractmethod
    def flushOutput(self):
        pass
    
