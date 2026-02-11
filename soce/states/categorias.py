import reflex as rx
from ..models import Categoria
from ..state import State

class CategoriaState(State):
    categorias: list[Categoria] = []
    new_cat_nombre: str = ""
    new_cat_descripcion: str = ""  # <-- AGREGAR este campo

    def load_categorias(self):  # <-- AGREGAR este método
        """Carga todas las categorías de la base de datos"""
        with rx.session() as session:
            self.categorias = session.exec(
                Categoria.select()
            ).all()

    def add_categoria(self):
        with rx.session() as session:
            if not self.new_cat_nombre:
                return rx.window_alert("Nombre obligatorio")
            
            nueva = Categoria(
                nombre=self.new_cat_nombre,
                descripcion=self.new_cat_descripcion  # <-- Incluir descripción
            )
            session.add(nueva)
            session.commit()
        
        # Limpia los campos
        self.new_cat_nombre = ""
        self.new_cat_descripcion = ""
        
        # Recarga las categorías
        self.load_categorias()  # <-- CAMBIAR esto en lugar de State.on_load