from abc import ABC, abstractmethod

class TTSInterface(ABC):
    @abstractmethod
    def get_tts(self, text: str, voice_id: str, model: str = None) -> bytes:
        pass
