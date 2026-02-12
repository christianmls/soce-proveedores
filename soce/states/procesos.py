import reflex as rx
from typing import Optional, List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime

class ProcesosState(State):
    # Variables de estado
    proceso_url_id: str = ""
    categoria_id: str = ""
    nuevo_codigo_proceso: str = ""
    nuevo_nombre_proceso: str = ""
    is_scraping: bool = False
    scraping_progress: str = "Listo para iniciar"
    
    categorias: list[Categoria] = []
    procesos: list[Proceso] = []
    proceso_actual: Optional[Proceso] = None
    barridos: list[Barrido] = []
    ofertas_actuales: list[Oferta] = []
    barrido_seleccionado_id: Optional[int] = None

    @rx.var
    def proceso_id(self) -> int:
        """Parámetro de ruta dinámico"""
        return int(self.router.page.params.get("proceso_id", 0))

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
        """Evita el error 'VarAttributeError' pre-procesando los strings"""
        return [
            {
                "id": str(p.id),
                "codigo_corto": (p.codigo_proceso[:30] + "...") if len(p.codigo_proceso) > 30 else p.codigo_proceso,
                "nombre": p.nombre if p.nombre else "-",
                "fecha": p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else "-"
            }
            for p in self.procesos
        ]

    @rx.var
    def barridos_formateados(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": str(b.id),
                "fecha_inicio": b.fecha_inicio.strftime("%Y-%m-%d %H:%M") if b.fecha_inicio else "-",
                "fecha_fin": b.fecha_fin.strftime("%H:%M") if b.fecha_fin else "En curso",
                "total": str(b.total_proveedores),
                "exitosos": str(b.exitosos),
                "estado": b.estado
            }
            for b in self.barridos
        ]

    @rx.var
    def ofertas_formateadas(self) -> List[Dict[str, Any]]:
        return [
            {
                "ruc": o.ruc_proveedor,
                "razon_social": o.razon_social or "-",
                "ubicacion": f"{o.pais} - {o.provincia}",
                "producto": o.descripcion_producto or "-",
                "cantidad": f"{o.cantidad:.2f}",
                "v_unitario": f"{o.valor_unitario:,.2f}",
                "v_total": f"{o.valor_total:,.2f}",
                "estado": o.estado
            }
            for o in self.ofertas_actuales if o.estado == "procesado"
        ]

    # --- Acciones ---
    def load_procesos(self):
        with rx.session() as session:
            self.procesos = session.exec(Proceso.select()).all()

    def set_barrido_seleccionado(self, b_id: str):
        self.barrido_seleccionado_id = int(b_id)
        self.cargar_ofertas_barrido()

    def load_proceso_detalle(self):
        pid = self.proceso_id
        if not pid: return
        with rx.session() as session:
            self.proceso_actual = session.get(Proceso, pid)
            self.barridos = session.exec(Barrido.select().where(Barrido.proceso_id == pid)).all()
        self.load_categorias()

    def load_categorias(self):
        with rx.session() as session:
            self.categorias = session.exec(Categoria.select()).all()

    def cargar_ofertas_barrido(self):
        if not self.barrido_seleccionado_id: return
        with rx.session() as session:
            self.ofertas_actuales = session.exec(
                Oferta.select().where(Oferta.barrido_id == self.barrido_seleccionado_id)
            ).all()

    def set_nuevo_codigo_proceso(self, v): self.nuevo_codigo_proceso = v
    def set_nuevo_nombre_proceso(self, v): self.nuevo_nombre_proceso = v
    def set_categoria_id(self, v): self.categoria_id = v