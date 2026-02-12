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
    proceso_id: str
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
    fecha_barrido: Optional[datetime] = None
    estado: str = "pendiente"
    tiene_archivos: bool = False
    
    # JSON con todos los datos
    datos_completos_json: Optional[str] = ""