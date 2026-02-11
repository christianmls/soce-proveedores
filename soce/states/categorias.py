import reflex as rx
from ..models import Categoria
from ..state import State # Importamos el base para disparar on_load

class CategoriaState(State):
    categorias: list[Categoria] = []
    new_cat_nombre: str = ""

    def add_categoria(self):
        with rx.session() as session:
            if not self.new_cat_nombre:
                return rx.window_alert("Nombre obligatorio")
            session.add(Categoria(nombre=self.new_cat_nombre))
            session.commit()
        self.new_cat_nombre = ""
        return State.on_load # Llama a la recarga global