import reflex as rx
from typing import List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Anexo, Proveedor, Categoria
from ..state import State
from sqlmodel import select, desc, delete
from datetime import datetime
from ..utils.scraper import scrape_proceso
import asyncio

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

    def set_current_view(self, val: str): self.current_view = val
    def set_nuevo_codigo_proceso(self, val: str): self.nuevo_codigo_proceso = val
    def set_nuevo_nombre_proceso(self, val: str): self.nuevo_nombre_proceso = val
    def set_categoria_id(self, val: str): self.categoria_id = val

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
        return [{"id": str(p.id), "codigo": p.codigo_proceso, "fecha": p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else "-"} for p in self.procesos]

    @rx.var
    def rucs_unicos(self) -> List[str]:
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
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        self.load_procesos()

    def eliminar_proceso(self, p_id: str):
        with rx.session() as session:
            barridos = session.exec(select(Barrido).where(Barrido.proceso_id == int(p_id))).all()
            for b in barridos:
                session.exec(delete(Oferta).where(Oferta.barrido_id == b.id))
                session.exec(delete(Anexo).where(Anexo.barrido_id == b.id))
                session.delete(b)
            proc = session.get(Proceso, int(p_id))
            if proc: session.delete(proc)
            session.commit()
        self.load_procesos()

    def load_proceso_detalle(self):
        self.ofertas_actuales = []
        self.anexos_actuales = []
        
        with rx.session() as session:
            proc = session.get(Proceso, self.proceso_id)
            if proc:
                self.proceso_url_id = proc.codigo_proceso
                self.categoria_id = str(proc.categoria_id)
                ultimo_b = session.exec(select(Barrido).where(Barrido.proceso_id == self.proceso_id).order_by(desc(Barrido.id))).first()
                if ultimo_b:
                    self.ofertas_actuales = session.exec(select(Oferta).where(Oferta.barrido_id == ultimo_b.id)).all()
                    self.anexos_actuales = session.exec(select(Anexo).where(Anexo.barrido_id == ultimo_b.id)).all()

    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.load_proceso_detalle()
        self.current_view = "detalle_proceso"

    async def iniciar_scraping(self):
        if not self.categoria_id: 
            self.scraping_progress = "❌ Selecciona una categoría"
            return
            
        self.is_scraping = True
        self.scraping_progress = "🔄 Iniciando barrido..."
        yield
        
        try:
            with rx.session() as session:
                # Crear barrido
                barrido = Barrido(proceso_id=self.proceso_id, fecha_inicio=datetime.now(), estado="en_proceso")
                session.add(barrido)
                session.commit()
                session.refresh(barrido)
                barrido_id = barrido.id
                
                # Obtener proveedores
                provs = session.exec(select(Proveedor).where(Proveedor.categoria_id == int(self.categoria_id))).all()
                total_p = len(provs)
                
                if total_p == 0:
                    self.scraping_progress = "⚠️ No hay proveedores en esta categoría"
                    barrido.estado = "completado"
                    barrido.fecha_fin = datetime.now()
                    session.commit()
                    self.is_scraping = False
                    yield
                    return

                exitosos = 0
                errores = 0
                
                for i, p in enumerate(provs, 1):
                    self.scraping_progress = f"({i}/{total_p}) Procesando RUC: {p.ruc}"
                    yield
                    
                    try:
                        # Timeout de 60 segundos por proveedor
                        res = await asyncio.wait_for(
                            scrape_proceso(self.proceso_url_id, p.ruc),
                            timeout=60.0
                        )
                        
                        if res and res.get("items"):
                            for it in res["items"]:
                                session.add(Oferta(
                                    barrido_id=barrido_id, 
                                    ruc_proveedor=p.ruc,
                                    razon_social=p.nombre or "",
                                    numero_item=it["numero"], 
                                    cpc=it["cpc"], 
                                    descripcion_producto=it["desc"], 
                                    unidad=it["unid"], 
                                    cantidad=it["cant"], 
                                    valor_unitario=it["v_unit"], 
                                    valor_total=it["v_tot"],
                                    fecha_scraping=datetime.now()
                                ))
                            
                            for an in res.get("anexos", []):
                                session.add(Anexo(
                                    barrido_id=barrido_id, 
                                    ruc_proveedor=p.ruc, 
                                    nombre_archivo=an["nombre"], 
                                    url_archivo=an["url"],
                                    fecha_registro=datetime.now()
                                ))
                            
                            session.commit()
                            exitosos += 1
                        else:
                            self.scraping_progress = f"⚪ ({i}/{total_p}) Sin ofertas: {p.ruc}"
                            
                    except asyncio.TimeoutError:
                        errores += 1
                        self.scraping_progress = f"⏱️ ({i}/{total_p}) Timeout: {p.ruc}"
                        yield
                        
                    except Exception as e:
                        errores += 1
                        self.scraping_progress = f"❌ ({i}/{total_p}) Error: {p.ruc} - {str(e)}"
                        yield
                    
                    # Pausa entre requests
                    await asyncio.sleep(1)
                
                # Finalizar barrido
                barrido.estado = "completado"
                barrido.fecha_fin = datetime.now()
                session.commit()
                
            # Recargar datos
            self.load_proceso_detalle()
            self.scraping_progress = f"✅ Completado: {exitosos} exitosos, {errores} errores"
            
        except Exception as e:
            self.scraping_progress = f"❌ Error general: {str(e)}"
            
        finally:
            self.is_scraping = False
            yield