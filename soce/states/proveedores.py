import reflex as rx
from ..models import Proveedor, Categoria
from ..state import State

class ProveedoresState(State):
    proveedores: list[Proveedor] = []
    categorias: list[Categoria] = []  # <-- AGREGAR ESTA LÍNEA
    
    new_prov_ruc: str = ""
    new_prov_nombre: str = ""
    new_prov_cat_id: str = ""

    def set_new_prov_ruc(self, val: str): 
        self.new_prov_ruc = val
    
    def set_new_prov_nombre(self, val: str): 
        self.new_prov_nombre = val
    
    def set_new_prov_cat_id(self, val: str): 
        self.new_prov_cat_id = val

    def load_categorias(self):  # <-- AGREGAR ESTE MÉTODO
        """Carga todas las categorías disponibles"""
        with rx.session() as session:
            self.categorias = session.exec(
                Categoria.select()
            ).all()

    def load_proveedores(self):  # <-- AGREGAR ESTE MÉTODO
        """Carga todos los proveedores"""
        with rx.session() as session:
            self.proveedores = session.exec(
                Proveedor.select()
            ).all()

    def add_proveedor(self):
        with rx.session() as session:
            if not self.new_prov_ruc:
                return rx.window_alert("El RUC es obligatorio")
            
            nuevo = Proveedor(
                ruc=self.new_prov_ruc,
                nombre=self.new_prov_nombre,
                categoria_id=int(self.new_prov_cat_id) if self.new_prov_cat_id else None
            )
            session.add(nuevo)
            session.commit()
            
        # Reset de campos
        self.new_prov_ruc = ""
        self.new_prov_nombre = ""
        self.new_prov_cat_id = ""
        
        # Recarga los proveedores
        self.load_proveedores()