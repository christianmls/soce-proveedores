import reflex as rx
from typing import Optional, List
from ..models import Proceso, Barrido, Oferta, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime

class ProcesosState(State):
    # Datos de configuración
    proceso_url_id: str = ""
    categoria_id: str = ""
    
    # Nuevo proceso
    nuevo_codigo_proceso: str = ""
    nuevo_nombre_proceso: str = ""
    
    # Control del scraping
    is_scraping: bool = False
    scraping_progress: str = "Listo para iniciar"
    
    # Datos
    categorias: list[Categoria] = []
    procesos: list[Proceso] = []
    proceso_actual: Optional[Proceso] = None
    barridos: list[Barrido] = []
    ofertas_actuales: list[Oferta] = []
    
    # Barrido seleccionado
    barrido_seleccionado_id: Optional[int] = None
    
    # ID del proceso actual
    current_proceso_id: Optional[int] = None

    # --- COMPUTED VARS PARA LA VISTA ---

    @rx.var
    def proceso_id(self) -> int:
        """Obtiene el proceso_id de los parámetros de la ruta dinámicamente"""
        return int(self.router.page.params.get("proceso_id", 0))

    @rx.var
    def lista_procesos_formateada(self) -> List[dict]:
        """Pre-procesa la lista para evitar lógica compleja en el frontend"""
        return [
            {
                "id": p.id,
                "codigo_proceso": p.codigo_proceso,
                "codigo_corto": (p.codigo_proceso[:30] + "...") if len(p.codigo_proceso) > 30 else p.codigo_proceso,
                "nombre_display": p.nombre if p.nombre else "-",
                "fecha_creacion": p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else "-"
            }
            for p in self.procesos
        ]

    # --- SETTERS ---

    def set_proceso_url_id(self, val: str):
        self.proceso_url_id = val
    
    def set_categoria_id(self, val: str):
        self.categoria_id = val
    
    def set_nuevo_codigo_proceso(self, val: str):
        self.nuevo_codigo_proceso = val
    
    def set_nuevo_nombre_proceso(self, val: str):
        self.nuevo_nombre_proceso = val
    
    def set_barrido_seleccionado(self, barrido_id: int):
        self.barrido_seleccionado_id = barrido_id
        self.cargar_ofertas_barrido()

    # --- ACCIONES DE DATOS ---

    def load_categorias(self):
        with rx.session() as session:
            self.categorias = session.exec(Categoria.select()).all()

    def load_procesos(self):
        with rx.session() as session:
            self.procesos = session.exec(Proceso.select()).all()
    
    def crear_proceso(self):
        if not self.nuevo_codigo_proceso:
            return
        
        with rx.session() as session:
            proceso = Proceso(
                codigo_proceso=self.nuevo_codigo_proceso,
                nombre=self.nuevo_nombre_proceso,
                fecha_creacion=datetime.now()
            )
            session.add(proceso)
            session.commit()
        
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        self.load_procesos()
    
    def load_proceso_detalle(self):
        pid = self.proceso_id
        if not pid: return
        
        with rx.session() as session:
            self.proceso_actual = session.get(Proceso, pid)
            if self.proceso_actual:
                self.proceso_url_id = self.proceso_actual.codigo_proceso
                self.barridos = session.exec(
                    Barrido.select().where(Barrido.proceso_id == pid)
                ).all()
        self.load_categorias()

    def load_barridos(self):
        pid = self.proceso_id
        if not pid: return
        with rx.session() as session:
            self.barridos = session.exec(
                Barrido.select().where(Barrido.proceso_id == pid)
            ).all()

    def cargar_ofertas_barrido(self):
        if not self.barrido_seleccionado_id:
            self.ofertas_actuales = []
            return
        with rx.session() as session:
            self.ofertas_actuales = session.exec(
                Oferta.select().where(Oferta.barrido_id == self.barrido_seleccionado_id)
            ).all()

    # --- SCRAPING LOGIC ---

    async def iniciar_scraping(self):
        pid = self.proceso_id
        if not pid or not self.categoria_id:
            self.scraping_progress = "❌ Error: Verifique proceso y categoría"
            return
        
        self.is_scraping = True
        self.scraping_progress = "🔄 Iniciando..."
        yield

        # (Mantén aquí tu lógica de scraping igual que la tenías, 
        # pero asegúrate de usar self.proceso_id para obtener el ID)
        
        # ... Resto del código de scraping ...
        self.is_scraping = False
        yield