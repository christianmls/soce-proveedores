import reflex as rx
from ..models import Proceso
from ..state import State # Importante: heredar de TU State base

class ProcesosState(State):
    # Variables específicas de esta vista
    url_base: str = ""
    
    # El setter que falta
    def set_url_base(self, val: str):
        self.url_base = val
        
    def run_sweep(self):
        self.is_running = True # Heredado de State base
        self.logs = f"Analizando: {self.url_base}" # Heredado de State base
        yield
        # Lógica de scraping futura
        self.is_running = False