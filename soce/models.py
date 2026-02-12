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
    """Proceso de contratación pública"""
    codigo_proceso: str  # ID del proceso (ej: xrMof7bBhVx...)
    nombre: Optional[str] = ""
    objeto: Optional[str] = ""
    entidad: Optional[str] = ""
    fecha_creacion: Optional[datetime] = None

class Barrido(rx.Model, table=True):
    """Cada ejecución de scraping sobre un proceso"""
    proceso_id: int = Field(foreign_key="proceso.id")
    categoria_id: int = Field(foreign_key="categoria.id")
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: str = "en_proceso"  # en_proceso, completado, error
    total_proveedores: int = 0
    exitosos: int = 0
    sin_datos: int = 0
    errores: int = 0

class Oferta(rx.Model, table=True):
    """Oferta de un proveedor en un barrido específico"""
    barrido_id: int = Field(foreign_key="barrido.id")
    ruc_proveedor: str
    
    # Datos del proveedor
    razon_social: Optional[str] = ""
    correo_electronico: Optional[str] = ""
    telefono: Optional[str] = ""
    pais: Optional[str] = ""
    provincia: Optional[str] = ""
    canton: Optional[str] = ""
    direccion: Optional[str] = ""
    
    # Datos del producto/servicio
    descripcion_producto: Optional[str] = ""
    unidad: Optional[str] = ""
    cantidad: Optional[float] = 0.0
    valor_unitario: Optional[float] = 0.0
    valor_total: Optional[float] = 0.0
    
    # Metadatos
    fecha_scraping: Optional[datetime] = None
    estado: str = "pendiente"  # procesado, sin_datos, error
    tiene_archivos: bool = False
    datos_completos_json: Optional[str] = ""