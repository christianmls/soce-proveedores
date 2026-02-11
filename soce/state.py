import reflex as rx
from typing import List
from .models import Proceso, Categoria, Proveedor

class State(rx.State):
    # --- Variables de Navegación y Control ---
    current_page: str = "procesos"
    is_running: bool = False
    logs: str = "Esperando inicio..."
    url_base: str = ""

    # --- Listas de datos ---
    procesos: List[Proceso] = []
    categorias: List[Categoria] = []
    proveedores: List[Proveedor] = []
    
    # --- Variables para Formularios ---
    new_cat_nombre: str = ""
    new_prov_ruc: str = ""
    new_prov_nombre: str = ""

    # --- Setters Explícitos (Evitan DeprecationWarnings) ---
    def set_url_base(self, val: str):
        self.url_base = val

    def set_new_cat_nombre(self, val: str):
        self.new_cat_nombre = val

    def set_new_prov_ruc(self, val: str):
        self.new_prov_ruc = val

    def set_new_prov_nombre(self, val: str):
        self.new_prov_nombre = val

    # --- Lógica de Navegación y Carga ---
    def set_page(self, page: str):
        self.current_page = page
        return State.on_load

    @rx.event
    def on_load(self):
        with rx.session() as session:
            self.procesos = session.query(Proceso).all()
            self.categorias = session.query(Categoria).all()
            self.proveedores = session.query(Proveedor).all()

    # --- Funciones CRUD ---
    def add_categoria(self):
        with rx.session() as session:
            if not self.new_cat_nombre:
                return rx.window_alert("El nombre es obligatorio")
            nueva = Categoria(nombre=self.new_cat_nombre)
            session.add(nueva)
            session.commit()
        self.new_cat_nombre = ""
        return State.on_load

    def add_proveedor(self):
        with rx.session() as session:
            if not self.new_prov_ruc or not self.new_prov_nombre:
                return rx.window_alert("RUC y Nombre son obligatorios")
            nuevo = Proveedor(ruc=self.new_prov_ruc, nombre=self.new_prov_nombre)
            session.add(nuevo)
            session.commit()
        self.new_prov_ruc = ""
        self.new_prov_nombre = ""
        return State.on_load

    # --- Lógica del Scraper ---
    def run_sweep(self):
        self.is_running = True
        self.logs = f"Iniciando scraper para: {self.url_base}"
        yield
        # Espacio para la lógica de Playwright
        self.is_running = False
        self.logs += "\nBarrido finalizado."
