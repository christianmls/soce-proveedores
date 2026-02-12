import reflex as rx
from typing import Optional, List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime
from sqlmodel import select, desc
from ..utils.scraper import scrape_proceso

class ProcesosState(State):
    current_view: str = "procesos"
    proceso_id: int = 0
    proceso_url_id: str = "" 
    nuevo_codigo_proceso: str = ""
    nuevo_nombre_proceso: str = ""
    categoria_id: str = ""
    nombre_categoria_actual: str = ""
    is_scraping: bool = False
    scraping_progress: str = ""
    
    categorias: list[Categoria] = []
    procesos: list[Proceso] = []
    proceso_actual: Optional[Proceso] = None
    ofertas_actuales: list[Oferta] = []
    barrido_actual_id: Optional[int] = None

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": str(p.id),
                "codigo_corto": (p.codigo_proceso[:35] + "...") if p.codigo_proceso else "-",
                "nombre": p.nombre or "-",
                # FIX: Verificación de None para evitar AttributeError strftime
                "fecha": p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else "-"
            }
            for p in self.procesos
        ]

    @rx.var
    def ofertas_formateadas(self) -> List[Dict[str, Any]]:
        return [
            {
                "ruc": o.ruc_provider if hasattr(o, 'ruc_provider') else o.ruc_proveedor,
                "razon_social": o.razon_social or "N/D",
                "correo": o.correo_electronico or "S/N",
                "ubicacion": f"{o.pais or ''} {o.provincia or ''}".strip() or "-",
                "direccion": o.direccion or "-",
                "producto": o.descripcion_producto or "-",
                "unidad": o.unidad or "-",
                "cantidad": f"{o.cantidad:.2f}",
                "v_unitario": f"{o.valor_unitario:,.2f}",
                "v_total": f"{o.valor_total:,.2f}",
                "tiene_archivos": o.tiene_archivos,
                "estado": o.estado
            }
            for o in self.ofertas_actuales
        ]
    
    @rx.var
    def tiene_ofertas(self) -> bool:
        return len(self.ofertas_actuales) > 0

    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.scraping_progress = ""
        self.is_scraping = False 
        self.load_proceso_detalle()
        self.current_view = "detalle_proceso"

    def volver_a_lista(self):
        self.current_view = "procesos"
        self.proceso_id = 0
        self.ofertas_actuales = []
        self.is_scraping = False

    def load_procesos(self):
        with rx.session() as session:
            self.procesos = session.exec(select(Proceso).order_by(desc(Proceso.fecha_creacion))).all()
            
    def load_categorias(self):
        with rx.session() as session:
            self.categorias = session.exec(select(Categoria)).all()

    def crear_proceso(self):
        if not self.nuevo_codigo_proceso or not self.categoria_id: return
        with rx.session() as session:
            proceso = Proceso(
                codigo_proceso=self.nuevo_codigo_proceso,
                nombre=self.nuevo_nombre_proceso,
                fecha_creacion=datetime.now(),
                categoria_id=int(self.categoria_id)
            )
            session.add(proceso)
            session.commit()
        self.load_procesos()

    def load_proceso_detalle(self):
        self.is_scraping = False
        if not self.proceso_id: return
        with rx.session() as session:
            self.proceso_actual = session.get(Proceso, self.proceso_id)
            if self.proceso_actual:
                self.proceso_url_id = self.proceso_actual.codigo_proceso
                cat = session.get(Categoria, self.proceso_actual.categoria_id)
                self.nombre_categoria_actual = cat.nombre if cat else "N/D"
                
                ultimo_barrido = session.exec(
                    select(Barrido).where(Barrido.proceso_id == self.proceso_id).order_by(desc(Barrido.id))
                ).first()

                if ultimo_barrido:
                    self.ofertas_actuales = session.exec(
                        select(Oferta).where(Oferta.barrido_id == ultimo_barrido.id)
                    ).all()
                    fecha_txt = ultimo_barrido.fecha_fin.strftime('%d/%m %H:%M') if ultimo_barrido.fecha_fin else "Reciente"
                    self.scraping_progress = f"📅 Datos del último barrido ({fecha_txt})"
                else:
                    self.ofertas_actuales = []
                    self.scraping_progress = "No hay datos previos."

    async def iniciar_scraping(self):
        if not self.proceso_id or self.is_scraping: return
        self.is_scraping = True
        self.scraping_progress = "🔄 Iniciando..."
        yield

        try:
            with rx.session() as session:
                barrido = Barrido(proceso_id=self.proceso_id, fecha_inicio=datetime.now())
                session.add(barrido)
                session.commit()
                session.refresh(barrido)
                barrido_id = barrido.id

                proveedores = session.exec(select(Proveedor).where(Proveedor.categoria_id == int(self.categoria_id))).all()
                total = len(proveedores)

                for i, prov in enumerate(proveedores, 1):
                    self.scraping_progress = f"🔍 ({i}/{total}) Consultando: {prov.ruc}..."
                    yield
                    items = await scrape_proceso(self.proceso_url_id, prov.ruc)
                    
                    if items:
                        for item in items:
                            session.add(Oferta(
                                barrido_id=barrido_id,
                                ruc_proveedor=prov.ruc,
                                razon_social=item.get('razon_social', prov.nombre),
                                correo_electronico=item.get('correo_electronico', ''),
                                descripcion_producto=item.get('descripcion_producto', ''),
                                unidad=item.get('unidad', ''),
                                cantidad=item.get('cantidad', 0.0),
                                valor_unitario=item.get('valor_unitario', 0.0),
                                valor_total=item.get('valor_total', 0.0),
                                tiene_archivos=item.get('tiene_archivos', False),
                                estado="procesado",
                                fecha_scraping=datetime.now()
                            ))
                    else:
                        session.add(Oferta(barrido_id=barrido_id, ruc_proveedor=prov.ruc, estado="sin_datos"))
                    session.commit()

                barrido.estado = "completado"
                barrido.fecha_fin = datetime.now()
                session.commit()
            self.load_proceso_detalle()
        finally:
            self.is_scraping = False