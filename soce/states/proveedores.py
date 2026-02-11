import reflex as rx
from ..models import Proveedor
from ..state import State

class ProveedoresState(State):
    proveedores: list[Proveedor] = []
    new_prov_ruc: str = ""
    new_prov_nombre: str = ""
    # Variable para capturar el ID de la categoría seleccionada
    new_prov_cat_id: str = ""

    def set_new_prov_ruc(self, val: str): self.new_prov_ruc = val
    def set_new_prov_nombre(self, val: str): self.new_prov_nombre = val
    def set_new_prov_cat_id(self, val: str): self.new_prov_cat_id = val

    def add_proveedor(self):
        with rx.session() as session:
            if not self.new_prov_ruc:
                return rx.window_alert("El RUC es obligatorio")
            
            nuevo = Proveedor(
                ruc=self.new_prov_ruc,
                nombre=self.new_prov_nombre,
                # Convertimos a int si hay una categoría seleccionada
                categoria_id=int(self.new_prov_cat_id) if self.new_prov_cat_id else None
            )
            session.add(nuevo)
            session.commit()
            
        # Reset de campos
        self.new_prov_ruc = ""
        self.new_prov_nombre = ""
        self.new_prov_cat_id = ""
        return State.on_load