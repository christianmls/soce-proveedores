import reflex as rx
from typing import Optional

class Categoria(rx.Model, table=True):
    nombre: str
    descripcion: str = ""

class Proveedor(rx.Model, table=True):
    # Definición de la Clave Foránea
    categoria_id: int = rx.Field(default=None, foreign_key="categoria.id")    
    ruc: str
    # El nombre ahora es opcional (nullable)
    nombre: Optional[str] = "" 

class Proceso(rx.Model, table=True):
    objeto: str
    valor: str
    proveedor_ruc: str
