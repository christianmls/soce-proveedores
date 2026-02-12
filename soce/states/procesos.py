import reflex as rx
from typing import List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Anexo, Proveedor, Categoria
from ..state import State
from sqlmodel import select, desc
from datetime import datetime
from ..utils.scraper import scrape_proceso

class ProcesosState(State):
    current_view: str = "procesos"
    proceso_id: int = 0
    proceso_url_id: str = "" 
    categoria_id: str = ""
    is_scraping: bool = False
    scraping_progress: str = ""
    
    procesos: List[Proceso] = []
    categorias: List[Categoria] = []
    ofertas_actuales: List[Oferta] = []
    anexos_actuales: List[Anexo] = []

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
        return [{"id": str(p.id), "codigo": p.codigo_proceso, "fecha": p.fecha_creacion.strftime("%Y-%m-%d") if p.fecha_creacion else "-"} for p in self.procesos]

    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.load_proceso_detalle()
        self.current_view = "detalle_proceso"

    def load_procesos(self):
        with rx.session() as session:
            self.procesos = session.exec(select(Proceso).order_by(desc(Proceso.id))).all()
            self.categorias = session.exec(select(Categoria)).all()

    def load_proceso_detalle(self):
        with rx.session() as session:
            proc = session.get(Proceso, self.proceso_id)
            if proc:
                self.proceso_url_id = proc.codigo_proceso
                self.categoria_id = str(proc.categoria_id)
                
                ultimo_b = session.exec(select(Barrido).where(Barrido.proceso_id == self.proceso_id).order_by(desc(Barrido.id))).first()
                if ultimo_b:
                    self.ofertas_actuales = session.exec(select(Oferta).where(Oferta.barrido_id == ultimo_b.id)).all()
                    self.anexos_actuales = session.exec(select(Anexo).where(Anexo.barrido_id == ultimo_b.id)).all()

    async def iniciar_scraping(self):
        self.is_scraping = True
        yield
        try:
            with rx.session() as session:
                barrido = Barrido(proceso_id=self.proceso_id, fecha_inicio=datetime.now())
                session.add(barrido)
                session.commit()
                
                provs = session.exec(select(Proveedor).where(Proveedor.categoria_id == int(self.categoria_id))).all()
                for p in provs:
                    res = await scrape_proceso(self.proceso_url_id, p.ruc)
                    if res: # Solo guardamos si hay datos (Total > 0)
                        for it in res["items"]:
                            session.add(Oferta(
                                barrido_id=barrido.id, ruc_proveedor=p.ruc, razon_social=res["razon_social"],
                                numero_item=it["numero"], cpc=it["cpc"], descripcion_producto=it["descripcion"],
                                unidad=it["unidad"], cantidad=it["cantidad"], valor_unitario=it["v_unit"], valor_total=it["v_total"]
                            ))
                        for an in res["anexos"]:
                            session.add(Anexo(barrido_id=barrido.id, ruc_proveedor=p.ruc, nombre_archivo=an))
                
                barrido.estado = "completado"
                barrido.fecha_fin = datetime.now()
                session.commit()
            self.load_proceso_detalle()
        finally:
            self.is_scraping = False