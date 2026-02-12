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

    def set_current_view(self, val: str): 
        self.current_view = val
        
    def set_nuevo_codigo_proceso(self, val: str): 
        self.nuevo_codigo_proceso = val
        
    def set_nuevo_nombre_proceso(self, val: str): 
        self.nuevo_nombre_proceso = val
        
    def set_categoria_id(self, val: str): 
        self.categoria_id = val

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
        return [{
            "id": str(p.id), 
            "codigo": p.codigo_proceso, 
            "fecha": p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else "-"
        } for p in self.procesos]

    @rx.var
    def rucs_unicos(self) -> List[str]:
        return sorted(list(set(o.ruc_proveedor for o in self.ofertas_actuales)))

    def load_procesos(self):
        with rx.session() as session:
            self.procesos = session.exec(select(Proceso).order_by(desc(Proceso.id))).all()
            self.categorias = session.exec(select(Categoria)).all()

    def crear_proceso(self):
        if not self.nuevo_codigo_proceso or not self.categoria_id: 
            return
        with rx.session() as session:
            session.add(Proceso(
                codigo_proceso=self.nuevo_codigo_proceso, 
                nombre=self.nuevo_nombre_proceso, 
                fecha_creacion=datetime.now(), 
                categoria_id=int(self.categoria_id)
            ))
            session.commit()
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        self.load_procesos()

    def eliminar_proceso(self, p_id: str):
        """Elimina proceso y todos sus datos relacionados en cascada"""
        try:
            with rx.session() as session:
                barridos = session.exec(
                    select(Barrido).where(Barrido.proceso_id == int(p_id))
                ).all()
                
                for barrido in barridos:
                    session.exec(delete(Oferta).where(Oferta.barrido_id == barrido.id))
                    session.exec(delete(Anexo).where(Anexo.barrido_id == barrido.id))
                    session.commit()
                
                session.exec(delete(Barrido).where(Barrido.proceso_id == int(p_id)))
                session.commit()
                
                proceso = session.get(Proceso, int(p_id))
                if proceso:
                    session.delete(proceso)
                    session.commit()
                    
            self.load_procesos()
            
        except Exception as e:
            print(f"Error eliminando proceso: {e}")

    def load_proceso_detalle(self):
        """Carga el último barrido del proceso"""
        print(f"[DEBUG] Cargando detalle del proceso {self.proceso_id}")
        
        self.ofertas_actuales = []
        self.anexos_actuales = []
        
        with rx.session() as session:
            proc = session.get(Proceso, self.proceso_id)
            if proc:
                self.proceso_url_id = proc.codigo_proceso
                self.categoria_id = str(proc.categoria_id)
                
                ultimo_b = session.exec(
                    select(Barrido)
                    .where(Barrido.proceso_id == self.proceso_id)
                    .order_by(desc(Barrido.id))
                ).first()
                
                if ultimo_b:
                    print(f"[DEBUG] Último barrido ID: {ultimo_b.id}")
                    
                    ofertas = session.exec(
                        select(Oferta).where(Oferta.barrido_id == ultimo_b.id)
                    ).all()
                    
                    anexos = session.exec(
                        select(Anexo).where(Anexo.barrido_id == ultimo_b.id)
                    ).all()
                    
                    self.ofertas_actuales = list(ofertas)
                    self.anexos_actuales = list(anexos)
                    
                    print(f"[DEBUG] Cargadas {len(self.ofertas_actuales)} ofertas y {len(self.anexos_actuales)} anexos")
                else:
                    print(f"[DEBUG] No hay barridos para este proceso")

    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.load_proceso_detalle()
        self.current_view = "detalle_proceso"

    async def iniciar_scraping(self):
        """Inicia el scraping con mejor manejo de errores"""
        print(f"[DEBUG] ===== INICIO SCRAPING =====")
        print(f"[DEBUG] Proceso ID: {self.proceso_id}")
        print(f"[DEBUG] Categoría ID: {self.categoria_id}")
        
        if not self.categoria_id: 
            self.scraping_progress = "❌ Selecciona una categoría"
            print(f"[DEBUG] Error: Sin categoría")
            return
            
        self.is_scraping = True
        self.scraping_progress = "🔄 Iniciando barrido..."
        yield
        
        barrido_id = None
        
        try:
            # Crear sesión
            print(f"[DEBUG] Creando barrido...")
            with rx.session() as session:
                barrido = Barrido(
                    proceso_id=self.proceso_id, 
                    fecha_inicio=datetime.now(), 
                    estado="en_proceso"
                )
                session.add(barrido)
                session.commit()
                session.refresh(barrido)
                barrido_id = barrido.id
                print(f"[DEBUG] Barrido creado ID: {barrido_id}")
                
                # Obtener proveedores
                provs = session.exec(
                    select(Proveedor)
                    .where(Proveedor.categoria_id == int(self.categoria_id))
                ).all()
                
                total_p = len(provs)
                print(f"[DEBUG] Total proveedores: {total_p}")
                
                if total_p == 0:
                    self.scraping_progress = "⚠️ No hay proveedores en esta categoría"
                    barrido.estado = "completado"
                    barrido.fecha_fin = datetime.now()
                    session.commit()
                    self.is_scraping = False
                    yield
                    return

                exitosos = 0
                sin_datos = 0
                errores = 0
                
                for i, p in enumerate(provs, 1):
                    self.scraping_progress = f"({i}/{total_p}) Procesando: {p.ruc}"
                    print(f"[DEBUG] Procesando proveedor {i}/{total_p}: {p.ruc}")
                    yield
                    
                    try:
                        # Scraping con timeout
                        print(f"[DEBUG] Iniciando scraping para {p.ruc}")
                        res = await asyncio.wait_for(
                            scrape_proceso(self.proceso_url_id, p.ruc),
                            timeout=60.0
                        )
                        
                        print(f"[DEBUG] Resultado scraping: {res is not None}")
                        
                        if res and res.get("items"):
                            print(f"[DEBUG] Items encontrados: {len(res['items'])}")
                            print(f"[DEBUG] Anexos encontrados: {len(res.get('anexos', []))}")
                            
                            # Guardar ofertas
                            for it in res["items"]:
                                oferta = Oferta(
                                    barrido_id=barrido_id, 
                                    ruc_proveedor=p.ruc,
                                    razon_social=p.nombre or "",
                                    numero_item=it.get("numero", ""), 
                                    cpc=it.get("cpc", ""), 
                                    descripcion_producto=it.get("desc", ""), 
                                    unidad=it.get("unid", ""), 
                                    cantidad=it.get("cant", 0.0), 
                                    valor_unitario=it.get("v_unit", 0.0), 
                                    valor_total=it.get("v_tot", 0.0),
                                    fecha_scraping=datetime.now()
                                )
                                session.add(oferta)
                                print(f"[DEBUG] Oferta agregada: Item {it.get('numero')}, Total: {it.get('v_tot')}")
                            
                            # Guardar anexos
                            for an in res.get("anexos", []):
                                anexo = Anexo(
                                    barrido_id=barrido_id, 
                                    ruc_proveedor=p.ruc, 
                                    nombre_archivo=an.get("nombre", ""), 
                                    url_archivo=an.get("url", ""),
                                    fecha_registro=datetime.now()
                                )
                                session.add(anexo)
                                print(f"[DEBUG] Anexo agregado: {an.get('nombre')}")
                            
                            session.commit()
                            print(f"[DEBUG] Datos guardados en BD para {p.ruc}")
                            
                            exitosos += 1
                            self.scraping_progress = f"✅ ({i}/{total_p}) {p.ruc}: {len(res['items'])} items"
                        else:
                            sin_datos += 1
                            self.scraping_progress = f"⚪ ({i}/{total_p}) Sin ofertas: {p.ruc}"
                            print(f"[DEBUG] Sin datos para {p.ruc}")
                        
                        yield
                            
                    except asyncio.TimeoutError:
                        errores += 1
                        self.scraping_progress = f"⏱️ ({i}/{total_p}) Timeout: {p.ruc}"
                        print(f"[ERROR] Timeout en {p.ruc}")
                        yield
                        
                    except Exception as e:
                        errores += 1
                        self.scraping_progress = f"❌ ({i}/{total_p}) Error: {p.ruc}"
                        print(f"[ERROR] Exception en {p.ruc}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        yield
                    
                    # Pausa entre requests
                    await asyncio.sleep(2)
                
                # Finalizar barrido
                print(f"[DEBUG] Finalizando barrido...")
                barrido.estado = "completado"
                barrido.fecha_fin = datetime.now()
                session.commit()
                print(f"[DEBUG] Barrido completado")
                
            # Recargar datos
            print(f"[DEBUG] Recargando datos...")
            self.load_proceso_detalle()
            self.scraping_progress = f"✅ Completado: {exitosos} exitosos, {sin_datos} sin datos, {errores} errores"
            print(f"[DEBUG] ===== FIN SCRAPING =====")
            
        except Exception as e:
            self.scraping_progress = f"❌ Error general: {str(e)}"
            print(f"[ERROR] Error general: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.is_scraping = False
            print(f"[DEBUG] is_scraping = False")
            yield