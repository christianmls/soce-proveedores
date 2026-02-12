import reflex as rx
from typing import Optional, List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime
from sqlmodel import select, desc # IMPORTANTE: Necesario para ordenar por fecha/id

class ProcesosState(State):
    # --- NAVEGACIÓN ---
    current_view: str = "procesos"
    
    # --- VARIABLES DE DATOS ---
    proceso_id: int = 0
    proceso_url_id: str = "" # El código string (ej: xrMof...)
    
    # Datos de creación / edición
    nuevo_codigo_proceso: str = ""
    nuevo_nombre_proceso: str = ""
    categoria_id: str = "" # Usado para el select en creación y para scraping
    nombre_categoria_actual: str = "" # Para mostrar en el detalle (solo lectura)
    
    # Control de Scraping
    is_scraping: bool = False
    scraping_progress: str = ""
    
    # Listas y Objetos
    categorias: list[Categoria] = []
    procesos: list[Proceso] = []
    proceso_actual: Optional[Proceso] = None
    ofertas_actuales: list[Oferta] = [] # Aquí se cargarán las ofertas directamente
    
    # Identificador del barrido que se está mostrando
    barrido_actual_id: Optional[int] = None

    # --- COMPUTED VARS (Formateo para la vista) ---

    @rx.var
    def lista_procesos_formateada(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": str(p.id),
                "codigo_corto": (p.codigo_proceso[:35] + "...") if len(p.codigo_proceso) > 35 else p.codigo_proceso,
                "nombre": p.nombre if p.nombre else "-",
                "fecha": p.fecha_creacion.strftime("%Y-%m-%d %H:%M") if p.fecha_creacion else "-"
            }
            for p in self.procesos
        ]

    @rx.var
    def ofertas_formateadas(self) -> List[Dict[str, Any]]:
        """Prepara las ofertas para las tarjetas"""
        return [
            {
                "ruc": o.ruc_proveedor,
                "razon_social": o.razon_social or "Razón Social No Disponible",
                "correo": o.correo_electronico or "S/N",
                "telefono": o.telefono or "-",
                "ubicacion": f"{o.pais or ''} {o.provincia or ''} {o.canton or ''}".strip() or "-",
                "direccion": o.direccion or "-",
                "producto": o.descripcion_producto or "-",
                "unidad": o.unidad or "-",
                "cantidad": f"{o.cantidad:.2f}" if o.cantidad else "0",
                "v_unitario": f"{o.valor_unitario:,.2f}" if o.valor_unitario else "0.00",
                "v_total": f"{o.valor_total:,.2f}" if o.valor_total else "0.00",
                "tiene_archivos": o.tiene_archivos,
                "estado": o.estado
            }
            for o in self.ofertas_actuales
        ]
    
    @rx.var
    def tiene_ofertas(self) -> bool:
        return len(self.ofertas_actuales) > 0

    # --- ACCIONES DE NAVEGACIÓN ---

    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.scraping_progress = "" # Limpiar mensajes viejos
        self.load_proceso_detalle()
        self.current_view = "detalle_proceso"

    def volver_a_lista(self):
        self.current_view = "procesos"
        self.proceso_id = 0
        self.ofertas_actuales = []
        self.categoria_id = "" # Limpiar selección

    # --- SETTERS ---
    def set_nuevo_codigo_proceso(self, val: str): self.nuevo_codigo_proceso = val
    def set_nuevo_nombre_proceso(self, val: str): self.nuevo_nombre_proceso = val
    def set_categoria_id(self, val: str): self.categoria_id = val

    # --- LÓGICA DE CARGA DE DATOS ---

    def load_procesos(self):
        with rx.session() as session:
            # Ordenamos por fecha de creación descendente (los nuevos primero)
            self.procesos = session.exec(select(Proceso).order_by(desc(Proceso.fecha_creacion))).all()
            
    def load_categorias(self):
        with rx.session() as session:
            self.categorias = session.exec(select(Categoria)).all()

    def crear_proceso(self):
        if not self.nuevo_codigo_proceso: return
        
        # Validar que se haya seleccionado categoría
        if not self.categoria_id:
            # Aquí podrías poner un toast de error
            return

        with rx.session() as session:
            proceso = Proceso(
                codigo_proceso=self.nuevo_codigo_proceso,
                nombre=self.nuevo_nombre_proceso,
                fecha_creacion=datetime.now(),
                # Guardamos la categoría seleccionada en el modal
                categoria_id=int(self.categoria_id)
            )
            session.add(proceso)
            session.commit()
        
        # Limpiar formulario
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        self.categoria_id = ""
        self.load_procesos()

    def load_proceso_detalle(self):
        """Carga el proceso y AUTOMÁTICAMENTE busca el último barrido"""
        if not self.proceso_id: return
        
        with rx.session() as session:
            # 1. Cargar Proceso
            self.proceso_actual = session.get(Proceso, self.proceso_id)
            
            if self.proceso_actual:
                self.proceso_url_id = self.proceso_actual.codigo_proceso
                
                # Cargar nombre de categoría para mostrar
                if self.proceso_actual.categoria_id:
                    self.categoria_id = str(self.proceso_actual.categoria_id)
                    cat = session.get(Categoria, self.proceso_actual.categoria_id)
                    self.nombre_categoria_actual = cat.nombre if cat else "Categoría Desconocida"
                
                # 2. LOGICA MAGICA: Buscar el último barrido exitoso o completado
                ultimo_barrido = session.exec(
                    select(Barrido)
                    .where(Barrido.proceso_id == self.proceso_id)
                    .order_by(desc(Barrido.id)) # El ID más alto es el último
                ).first()

                if ultimo_barrido:
                    self.barrido_actual_id = ultimo_barrido.id
                    # Cargar ofertas de ese barrido
                    self.ofertas_actuales = session.exec(
                        select(Oferta).where(Oferta.barrido_id == ultimo_barrido.id)
                    ).all()
                    
                    if not self.is_scraping:
                        self.scraping_progress = f"📅 Datos del último barrido ({ultimo_barrido.fecha_fin.strftime('%d/%m %H:%M')})"
                else:
                    self.barrido_actual_id = None
                    self.ofertas_actuales = []
                    self.scraping_progress = "No hay datos previos. Inicia un barrido."

    # --- SCRAPING ---

    async def iniciar_scraping(self):
        pid = self.proceso_id
        if not pid or not self.categoria_id:
            self.scraping_progress = "❌ Error: Faltan datos"
            return
        
        self.is_scraping = True
        self.scraping_progress = "🔄 Conectando..."
        self.ofertas_actuales = [] # Limpiamos la vista para mostrar progreso limpio
        yield
        
        # 1. Crear Barrido
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

        # 2. Obtener Proveedores
        with rx.session() as session:
            proveedores = session.exec(
                select(Proveedor).where(Proveedor.categoria_id == int(self.categoria_id))
            ).all()

        if not proveedores:
            self.scraping_progress = "⚠️ No hay proveedores en esta categoría"
            self.is_scraping = False
            yield
            return
        
        # 3. Simulación de Scraping (Aquí conecta tu scraper real)
        total = len(proveedores)
        self.scraping_progress = f"🔍 Analizando {total} proveedores..."
        yield
        await asyncio.sleep(1.5) # Simulación
        
        # --- AQUÍ GUARDARÍAS LAS OFERTAS EN LA BD ---
        
        # 4. Finalizar
        with rx.session() as session:
             b = session.get(Barrido, barrido_id)
             b.estado = "completado"
             b.fecha_fin = datetime.now()
             b.total_proveedores = total
             session.commit()

        self.scraping_progress = "✅ Completado. Cargando resultados..."
        self.is_scraping = False
        
        # 5. Recargar para ver las nuevas ofertas
        self.load_proceso_detalle()