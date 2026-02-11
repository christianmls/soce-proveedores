import reflex as rx
from ..models import Proceso
from ..state import State # Importamos tu State base

class ProcesosState(State):
    # La variable que faltaba en este sub-estado
    procesos: list[Proceso] = []
    
    # Aseguramos que url_base también esté aquí para el input
    url_base: str = ""

    def set_url_base(self, val: str):
        self.url_base = val

    def run_sweep(self):
        self.is_running = True
        self.logs = f"Iniciando barrido en: {self.url_base}"
        yield
        # Aquí irá el código de Playwright
        self.is_running = False
        self.logs += "\nTarea completada."