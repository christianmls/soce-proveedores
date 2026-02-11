import reflex as rx

class Categoria(rx.Model, table=True):
    nombre: str
    descripcion: str = ""

class Proveedor(rx.Model, table=True):
    ruc: str
    nombre: str
    contacto: str = ""

class Proceso(rx.Model, table=True):
    objeto: str
    valor: str
    proveedor_ruc: str
