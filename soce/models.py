import reflex as rx
from typing import Optional
from sqlmodel import Field

class Categoria(rx.Model, table=True):
    nombre: str
    descripcion: str = ""

class Proveedor(rx.Model, table=True):
    ruc: str
    nombre: Optional[str] = ""
    contacto: str = ""
    
    # Usa Field de sqlmodel directamente para la clave foránea
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id")

class Proceso(rx.Model, table=True):
    objeto: str
    valor: str
    proveedor_ruc: str