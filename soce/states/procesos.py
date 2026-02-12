import reflex as rx
from typing import Optional, List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime

class ProcesosState(State):
    # --- CONTROL DE NAVEGACIÓN (NUEVO) ---
    # Valores posibles: "procesos", "categorias", "proveedores", "detalle_proceso"
    current_view: str = "procesos" 

    def set_view(self, view: str):
        self.current_view = view

    # --- VARIABLES DE ESTADO ---
    # YA NO ES UN COMPUTED VAR DE RUTA, AHORA ES UNA VARIABLE NORMAL
    proceso_id: int = 0 
    
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

    # --- COMPUTED VARS ---

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
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
                "sin_datos": str(b.sin_datos),
                "errores": str(b.errores),
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
                "correo": o.correo_electronico or "-",
                "telefono": o.telefono or "-",
                "ubicacion": f"{o.pais} - {o.provincia} - {o.canton}",
                "direccion": o.direccion or "-",
                "producto": o.descripcion_producto or "-",
                "unidad": o.unidad or "-",
                "cantidad": f"{o.cantidad:.2f}" if o.cantidad > 0 else "-",
                "v_unitario": f"{o.valor_unitario:,.2f}" if o.valor_unitario > 0 else "-",
                "v_total": f"{o.valor_total:,.2f}" if o.valor_total > 0 else "-",
                "tiene_archivos": o.tiene_archivos,
                "estado": o.estado
            }
            for o in self.ofertas_actuales if o.estado == "procesado"
        ]

    # --- ACCIONES DE NAVEGACIÓN ---

    def ir_a_detalle(self, p_id: str):
        """Selecciona un proceso y cambia la vista"""
        self.proceso_id = int(p_id)
        self.load_proceso_detalle() # Carga los datos inmediatamente
        self.current_view = "detalle_proceso" # Cambia la pantalla

    def volver_a_lista(self):
        """Regresa a la lista de procesos"""
        self.current_view = "procesos"
        self.proceso_id = 0
        self.proceso_actual = None

    # --- SETTERS ---
    def set_nuevo_codigo_proceso(self, val: str): self.nuevo_codigo_proceso = val
    def set_nuevo_nombre_proceso(self, val: str): self.nuevo_nombre_proceso = val
    def set_categoria_id(self, val: str): self.categoria_id = val
    
    def set_barrido_seleccionado(self, barrido_id: str):
        self.barrido_seleccionado_id = int(barrido_id)
        self.cargar_ofertas_barrido()

    # --- CARGA DE DATOS ---

    def load_procesos(self):
        with rx.session() as session:
            self.procesos = session.exec(Proceso.select()).all()
    
    def crear_proceso(self):
        if not self.nuevo_codigo_proceso: return
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
        # Ahora usa self.proceso_id (int) directamente, no parámetros de URL
        if not self.proceso_id: return
        
        with rx.session() as session:
            self.proceso_actual = session.get(Proceso, self.proceso_id)
            if self.proceso_actual:
                self.proceso_url_id = self.proceso_actual.codigo_proceso
                self.barridos = session.exec(Barrido.select().where(Barrido.proceso_id == self.proceso_id)).all()
        self.load_categorias()

    def load_categorias(self):
        with rx.session() as session:
            self.categorias = session.exec(Categoria.select()).all()

    def cargar_ofertas_barrido(self):
        if not self.barrido_seleccionado_id:
            self.ofertas_actuales = []
            return
        with rx.session() as session:
            self.ofertas_actuales = session.exec(
                Oferta.select().where(Oferta.barrido_id == self.barrido_seleccionado_id)
            ).all()

    # --- SCRAPING (Sin cambios en lógica interna) ---
    async def iniciar_scraping(self):
        pid = self.proceso_id
        if not pid or not self.categoria_id:
            self.scraping_progress = "❌ Error: Verifique proceso y categoría"
            return
        
        self.is_scraping = True
        self.scraping_progress = "🔄 Iniciando..."
        yield

        with rx.session() as session:
            barrido = Barrido(
                proceso_id=pid,
                categoria_id=int(self.categoria_id),
                fecha_inicio=datetime.now(),
                estado="en_proceso"
            )
            session.add(barrido)
            session.commit()
            session.refresh(barrido)
            barrido_id = barrido.id

        with rx.session() as session:
            proveedores = session.exec(
                Proveedor.select().where(Proveedor.categoria_id == int(self.categoria_id))
            ).all()

        if not proveedores:
            self.scraping_progress = "⚠️ No hay proveedores"
            self.is_scraping = False
            yield
            return
        
        # Simulación
        total = len(proveedores)
        self.scraping_progress = f"📋 Encontrados {total} proveedores..."
        yield
        await asyncio.sleep(1)

        with rx.session() as session:
            b = session.get(Barrido, barrido_id)
            b.estado = "completado"
            b.fecha_fin = datetime.now()
            b.total_proveedores = total
            session.commit()

        self.scraping_progress = "✅ Completado"
        self.is_scraping = False
        self.load_proceso_detalle()