import reflex as rx
from typing import List, Dict, Any, Optional
from ..models import Proceso, Barrido, Oferta, Anexo, Proveedor, Categoria
from ..state import State
from sqlmodel import select, desc
from datetime import datetime
from ..utils.scraper import scrape_proceso

class ProcesosState(State):
    current_view: str = "procesos"
    proceso_id: int = 0
    proceso_url_id: str = "" 
    nuevo_codigo_proceso: str = ""
    nuevo_nombre_proceso: str = ""
    categoria_id: str = ""
    is_scraping: bool = False
    scraping_progress: str = ""
    
    procesos: List[Proceso] = []
    categorias: List[Categoria] = []
    ofertas_actuales: List[Oferta] = []
    anexos_actuales: List[Anexo] = []

    def set_current_view(self, view: str): self.current_view = view
    def set_nuevo_codigo_proceso(self, val: str): self.nuevo_codigo_proceso = val
    def set_nuevo_nombre_proceso(self, val: str): self.nuevo_nombre_proceso = val
    def set_categoria_id(self, val: str): self.categoria_id = val

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
        return [{"id": str(p.id), "codigo": p.codigo_proceso, "fecha": p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else "-"} for p in self.procesos]

    @rx.var
    def rucs_unicos(self) -> List[str]:
        # Devuelve los RUCs de las ofertas cargadas para generar las tarjetas
        return sorted(list(set(o.ruc_proveedor for o in self.ofertas_actuales)))

    def load_procesos(self):
        with rx.session() as session:
            self.procesos = session.exec(select(Proceso).order_by(desc(Proceso.id))).all()
            self.categorias = session.exec(select(Categoria)).all()

    def crear_proceso(self):
        if not self.nuevo_codigo_proceso or not self.categoria_id: return
        with rx.session() as session:
            session.add(Proceso(codigo_proceso=self.nuevo_codigo_proceso, nombre=self.nuevo_nombre_proceso, fecha_creacion=datetime.now(), categoria_id=int(self.categoria_id)))
            session.commit()
        self.load_procesos()

    def load_proceso_detalle(self):
        with rx.session() as session:
            proc = session.get(Proceso, self.proceso_id)
            if proc:
                self.proceso_url_id = proc.codigo_proceso
                self.categoria_id = str(proc.categoria_id)
                # Buscamos el último barrido exitoso
                ultimo_b = session.exec(select(Barrido).where(Barrido.proceso_id == self.proceso_id).order_by(desc(Barrido.id))).first()
                if ultimo_b:
                    self.ofertas_actuales = session.exec(select(Oferta).where(Oferta.barrido_id == ultimo_b.id)).all()
                    self.anexos_actuales = session.exec(select(Anexo).where(Anexo.barrido_id == ultimo_b.id)).all()

    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.load_proceso_detalle()
        self.set_current_view("detalle_proceso")

    async def iniciar_scraping(self):
        self.is_scraping = True
        self.scraping_progress = "Iniciando..."
        self.ofertas_actuales = [] # Limpiar vista previa
        yield
        try:
            with rx.session() as session:
                barrido = Barrido(proceso_id=self.proceso_id, fecha_inicio=datetime.now())
                session.add(barrido)
                session.commit()
                session.refresh(barrido)
                
                provs = session.exec(select(Proveedor).where(Proveedor.categoria_id == int(self.categoria_id))).all()
                total = len(provs)

                for i, p in enumerate(provs, 1):
                    self.scraping_progress = f"({i}/{total}) Consultando: {p.ruc}"
                    yield
                    res = await scrape_proceso(self.proceso_url_id, p.ruc)
                    if res:
                        for it in res["items"]:
                            session.add(Oferta(
                                barrido_id=barrido.id, ruc_proveedor=p.ruc, razon_social=res["razon_social"],
                                numero_item=it["numero"], cpc=it["cpc"], descripcion_producto=it["descripcion"],
                                unidad=it["unidad"], cantidad=it["cantidad"], valor_unitario=it["v_unit"], valor_total=it["v_total"]
                            ))
                        for an in res["anexos"]:
                            session.add(Anexo(barrido_id=barrido.id, ruc_proveedor=p.ruc, nombre_archivo=an["nombre"], url_archivo=an["url"]))
                    session.commit()
                barrido.fecha_fin = datetime.now()
                barrido.estado = "completado"
                session.commit()
            
            # Recargar los datos inmediatamente al terminar
            self.load_proceso_detalle()
            self.scraping_progress = "Finalizado"
        except Exception as e:
            self.scraping_progress = f"Error: {e}"
        finally:
            self.is_scraping = False