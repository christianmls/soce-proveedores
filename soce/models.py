import reflex as rx
from typing import Optional
import sqlmodel

class Categoria(rx.Model, table=True):
    nombre: str
    descripcion: str = ""

class Proveedor(rx.Model, table=True):
    # 1. Definimos el RUC como campo obligatorio
    ruc: str
    
    # 2. El nombre con Optional y valor por defecto None para que sea Nullable
    nombre: Optional[str] = rx.Field(default=None)
    
    # 3. La Clave Foránea corregida:
    # Usamos Optional[int] y pasamos foreign_key como primer argumento posicional de Field si es necesario, 
    # o aseguramos que sqlmodel lo reconozca.
    categoria_id: Optional[int] = rx.Field(
        default=None, 
        sa_column=sqlmodel.Column(sqlmodel.Integer, sqlmodel.ForeignKey("categoria.id"), nullable=True)
    )

class Proceso(rx.Model, table=True):
    objeto: str
    valor: str
    proveedor_ruc: str