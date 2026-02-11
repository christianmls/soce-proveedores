import reflex as rx
from .models import Proceso, Categoria, Proveedor

class State(rx.State):
    current_page: str = "procesos"
    is_running: bool = False
    logs: str = "Esperando..."

    # ESTA ES LA FUNCIÓN QUE FALTA:
    def set_page(self, page: str):
        self.current_page = page

    @rx.event
    def on_load(self):
        # Esta función puede orquestar la carga de todos los sub-estados
        with rx.session() as session:
            pass