import reflex as rx
from typing import Optional
from sqlmodel import Field

from datetime import datetime
class Categoria(rx.Model, table=True):
    nombre: str
    descripcion: str = ""

class Proveedor(rx.Model, table=True):
    ruc: str
    nombre: Optional[str] = ""
    contacto: str = ""
    
    # Añade un nombre a la clave foránea usando sa_column_kwargs
    categoria_id: Optional[int] = Field(
        default=None, 
        foreign_key="categoria.id",
        sa_column_kwargs={"name": "categoria_id"}
    )

class Proceso(rx.Model, table=True):
    proceso_id: str  # El ID del proceso de compras públicas
    ruc_proveedor: str
    nombre_proveedor: Optional[str] = ""
    objeto_proceso: Optional[str] = ""
    valor_adjudicado: Optional[float] = 0.0
    fecha_barrido: datetime = Field(default_factory=datetime.now)
    estado: str = "pendiente"  # pendiente, procesado, error
    datos_json: Optional[str] = ""  # Para guardar datos adicionales