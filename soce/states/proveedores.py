import reflex as rx
from ..models import Proveedor, Categoria
from ..state import State

class ProveedoresState(State):
    proveedores: list[Proveedor] = []
    categorias: list[Categoria] = []
    
    new_prov_ruc: str = ""
    new_prov_nombre: str = ""
    new_prov_contacto: str = ""  # <-- AGREGAR
    new_prov_cat_id: str = ""

    def set_new_prov_ruc(self, val: str): 
        self.new_prov_ruc = val
    
    def set_new_prov_nombre(self, val: str): 
        self.new_prov_nombre = val
    
    def set_new_prov_contacto(self, val: str):  # <-- AGREGAR
        self.new_prov_contacto = val
    
    def set_new_prov_cat_id(self, val: str): 
        self.new_prov_cat_id = val

    def load_categorias(self):
        """Carga todas las categorías disponibles"""
        with rx.session() as session:
            self.categorias = session.exec(
                Categoria.select()
            ).all()

    def load_proveedores(self):
        """Carga todos los proveedores"""
        with rx.session() as session:
            self.proveedores = session.exec(
                Proveedor.select()
            ).all()
    
    def load_data(self):  # <-- AGREGAR método combinado
        """Carga categorías y proveedores"""
        self.load_categorias()
        self.load_proveedores()

    def add_proveedor(self):
        if not self.new_prov_ruc:
            return rx.window_alert("El RUC es obligatorio")
        
        with rx.session() as session:
            nuevo = Proveedor(
                ruc=self.new_prov_ruc,
                nombre=self.new_prov_nombre,
                contacto=self.new_prov_contacto,  # <-- AGREGAR
                categoria_id=int(self.new_prov_cat_id) if self.new_prov_cat_id else None
            )
            session.add(nuevo)
            session.commit()
            
        # Reset de campos
        self.new_prov_ruc = ""
        self.new_prov_nombre = ""
        self.new_prov_contacto = ""  # <-- AGREGAR
        self.new_prov_cat_id = ""
        
        # Recarga los proveedores
        self.load_proveedores()