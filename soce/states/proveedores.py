import reflex as rx
from ..models import Proveedor
from ..state import State

class ProveedorState(State):
    proveedores: list[Proveedor] = []
    new_prov_ruc: str = ""
    new_prov_nombre: str = ""
    new_prov_cat_id: str = ""

    def add_proveedor(self):
        with rx.session() as session:
            if not self.new_prov_ruc:
                return rx.window_alert("RUC obligatorio")
            nuevo = Proveedor(
                ruc=self.new_prov_ruc,
                nombre=self.new_prov_nombre,
                categoria_id=int(self.new_prov_cat_id) if self.new_prov_cat_id else None
            )
            session.add(nuevo)
            session.commit()
        self.new_prov_ruc = ""
        self.new_prov_nombre = ""
        return State.on_load