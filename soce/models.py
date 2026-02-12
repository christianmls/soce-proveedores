import reflex as rx
from typing import Optional
from sqlmodel import Field
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
    codigo_proceso: str
    nombre: Optional[str] = ""
    fecha_creacion: Optional[datetime] = None
    categoria_id: int = Field(foreign_key="categoria.id")

class Barrido(rx.Model, table=True):
    proceso_id: int = Field(foreign_key="proceso.id")    
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: str = "en_proceso"
    total_proveedores: int = 0
    exitosos: int = 0

class Oferta(rx.Model, table=True):
    """Guarda cada fila de la tabla de la web"""
    barrido_id: int = Field(foreign_key="barrido.id")
    ruc_proveedor: str
    razon_social: Optional[str] = ""
    
    # Columnas exactas de la web
    numero_item: str
    cpc: str
    descripcion_producto: str
    unidad: str
    cantidad: float
    valor_unitario: float
    valor_total: float
    
    fecha_scraping: Optional[datetime] = None

class Anexo(rx.Model, table=True):
    """Nueva tabla para documentos adjuntos"""
    barrido_id: int = Field(foreign_key="barrido.id")
    ruc_proveedor: str
    nombre_archivo: str
    # En estos sitios la URL suele ser dinámica, guardamos el nombre como referencia
    fecha_registro: datetime = Field(default_factory=datetime.now)