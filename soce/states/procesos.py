import reflex as rx
from typing import Optional, List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime
from sqlmodel import select, desc # Necesario para ordenar

class ProcesosState(State):
    # --- NAVEGACIÓN ---
    current_view: str = "procesos"
    proceso_id: int = 0
    proceso_url_id: str = ""
    
    # --- DATOS ---
    categoria_id: str = ""
    nombre_categoria_actual: str = "" # Para mostrar el nombre en el detalle (Solo lectura)
    
    nuevo_codigo_proceso: str = ""
    nuevo_nombre_proceso: str = ""
    is_scraping: bool = False
    scraping_progress: str = "" # Vacío por defecto
    
    categorias: list[Categoria] = []
    procesos: list[Proceso] = []
    proceso_actual: Optional[Proceso] = None
    ofertas_actuales: list[Oferta] = []
    
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
            # Mostramos ofertas procesadas o con errores, para tener feedback
            for o in self.ofertas_actuales 
        ]
    
    @rx.var
    def tiene_ofertas(self) -> bool:
        return len(self.ofertas_actuales) > 0

    # --- ACCIONES ---

    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.load_proceso_detalle()
        self.current_view = "detalle_proceso"

    def volver_a_lista(self):
        self.current_view = "procesos"
        self.proceso_id = 0
        self.ofertas_actuales = []
        self.scraping_progress = ""
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        self.categoria_id = ""

    # Setters
    def set_nuevo_codigo_proceso(self, val: str): self.nuevo_codigo_proceso = val
    def set_nuevo_nombre_proceso(self, val: str): self.nuevo_nombre_proceso = val
    def set_categoria_id(self, val: str): self.categoria_id = val

    # --- CARGA DE DATOS ---

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
                categoria_id=int(self.categoria_id) # Guardamos la categoría
            )
            session.add(proceso)
            session.commit()
        
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        self.categoria_id = ""
        self.load_procesos()

    def load_proceso_detalle(self):
        """Carga el proceso y AUTOMÁTICAMENTE las ofertas del último barrido"""
        if not self.proceso_id: return
        
        with rx.session() as session:
            # 1. Cargar datos del proceso
            self.proceso_actual = session.get(Proceso, self.proceso_id)
            if self.proceso_actual:
                self.proceso_url_id = self.proceso_actual.codigo_proceso
                
                # Cargar nombre de categoría para mostrarlo (Read-Only)
                if self.proceso_actual.categoria_id:
                    self.categoria_id = str(self.proceso_actual.categoria_id)
                    cat = session.get(Categoria, self.proceso_actual.categoria_id)
                    self.nombre_categoria_actual = cat.nombre if cat else "Desconocida"
                else:
                    self.nombre_categoria_actual = "Sin Categoría"

                # 2. BUSCAR EL ÚLTIMO BARRIDO (Lógica Clave)
                # Ordenamos por ID descendente para obtener el más reciente
                ultimo_barrido = session.exec(
                    select(Barrido)
                    .where(Barrido.proceso_id == self.proceso_id)
                    .order_by(desc(Barrido.id))
                ).first()

                if ultimo_barrido:
                    # Cargamos ofertas directamente
                    self.ofertas_actuales = session.exec(
                        select(Oferta).where(Oferta.barrido_id == ultimo_barrido.id)
                    ).all()
                    # Si acabamos de entrar, mostramos resumen del último estado
                    if not self.is_scraping:
                        self.scraping_progress = f"📅 Último barrido: {ultimo_barrido.fecha_fin.strftime('%d/%m %H:%M') if ultimo_barrido.fecha_fin else 'Reciente'}"
                else:
                    self.ofertas_actuales = []
                    self.scraping_progress = "No hay barridos previos. Inicia uno."

    # --- SCRAPING ---

    async def iniciar_scraping(self):
        pid = self.proceso_id
        if not pid or not self.categoria_id:
            self.scraping_progress = "❌ Error: Datos faltantes"
            return
        
        self.is_scraping = True
        self.scraping_progress = "🔄 Conectando con proveedores..."
        self.ofertas_actuales = [] # Limpiamos la vista anterior mientras carga
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
        
        # 3. Simulación de Scraping (Aquí va tu lógica real)
        total = len(proveedores)
        self.scraping_progress = f"🔍 Analizando {total} proveedores..."
        yield
        
        await asyncio.sleep(1.5) # Simulación de tiempo de carga
        
        # --- AQUÍ IRÍA TU CÓDIGO REAL DE SCRAPING QUE GUARDA LAS OFERTAS EN DB ---
        
        # 4. Finalizar
        with rx.session() as session:
             b = session.get(Barrido, barrido_id)
             b.estado = "completado"
             b.fecha_fin = datetime.now()
             b.total_proveedores = total
             session.commit()

        self.scraping_progress = "✅ Barrido completado exitosamente"
        self.is_scraping = False
        
        # 5. RECARGAR AUTOMÁTICAMENTE PARA MOSTRAR LAS NUEVAS OFERTAS
        self.load_proceso_detalle()