import reflex as rx
from ..models import Proceso
from ..state import State # El State base

class ProcesosState(State): # <--- Debe ser ProcesosState
    procesos: list[Proceso] = []
    
    def run_sweep(self):
        self.is_running = True
        self.logs = "Iniciando barrido modular..."
        yield
        # Lógica del scraper aquí
        self.is_running = False