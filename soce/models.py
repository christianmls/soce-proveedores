import reflex as rx
from typing import Optional
from sqlalchemy import Column, DateTime, func
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
    # Cambia esta línea para usar server_default en lugar de default_factory
    fecha_barrido: datetime = Field(
        default=None,
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    estado: str = "pendiente"  # pendiente, procesado, error
    datos_json: Optional[str] = ""  # Para guardar datos adicionales