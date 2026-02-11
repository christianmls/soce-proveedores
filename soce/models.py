import reflex as rx
from typing import Optional

class Categoria(rx.Model, table=True):
    nombre: str
    descripcion: str = ""

class Proveedor(rx.Model, table=True):
    ruc: str
    # Nombre opcional inicializado como vacío
    nombre: Optional[str] = "" 
    contacto: str = ""
    
    # FK corregida para Reflex:
    # SQLModel (que usa Reflex) prefiere 'foreign_key' directamente en rx.Field
    # Si 'foreign_key' falló antes, es usualmente por el tipo 'int' vs 'Optional[int]'
    categoria_id: Optional[int] = rx.Field(default=None, foreign_key="categoria.id")

class Proceso(rx.Model, table=True):
    objeto: str
    valor: str
    proveedor_ruc: str