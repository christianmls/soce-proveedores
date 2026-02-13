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
    correo: Optional[str] = ""
    telefono: Optional[str] = ""
    pais: Optional[str] = ""
    provincia: Optional[str] = ""
    canton: Optional[str] = ""
    direccion: Optional[str] = ""
    contacto: str = ""
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id")

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

class Oferta(rx.Model, table=True):
    barrido_id: int = Field(foreign_key="barrido.id")
    ruc_proveedor: str
    razon_social: Optional[str] = ""
    numero_item: str = ""
    cpc: str = ""
    descripcion_producto: str = ""
    unidad: str = ""
    cantidad: float = 0.0
    valor_unitario: float = 0.0
    valor_total: float = 0.0
    fecha_scraping: Optional[datetime] = None

class Anexo(rx.Model, table=True):
    barrido_id: int = Field(foreign_key="barrido.id")
    ruc_proveedor: str
    nombre_archivo: str
    url_archivo: str = ""
    fecha_registro: Optional[datetime] = None