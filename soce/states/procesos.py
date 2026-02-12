import reflex as rx
from typing import Optional, List, Dict, Any
from ..models import Proceso, Barrido, Oferta, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime
from sqlmodel import select, desc
# IMPORTANTE: Ajusta esta línea según dónde guardaste scraper.py
# Si está en la carpeta soce junto a soce.py:
from ..scraper import scrape_proceso 
# Si está en una carpeta utils: from ..utils.scraper import scrape_proceso

class ProcesosState(State):
    # --- NAVEGACIÓN ---
    current_view: str = "procesos"
    
    # --- VARIABLES ---
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

    # --- COMPUTED VARS ---
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

    # --- ACCIONES ---
    def ir_a_detalle(self, p_id: str):
        self.proceso_id = int(p_id)
        self.scraping_progress = ""
        self.load_proceso_detalle()
        self.current_view = "detalle_proceso"

    def volver_a_lista(self):
        self.current_view = "procesos"
        self.proceso_id = 0
        self.ofertas_actuales = []
        self.categoria_id = ""

    def set_nuevo_codigo_proceso(self, val: str): self.nuevo_codigo_proceso = val
    def set_nuevo_nombre_proceso(self, val: str): self.nuevo_nombre_proceso = val
    def set_categoria_id(self, val: str): self.categoria_id = val

    # --- CARGA ---
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
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        self.categoria_id = ""
        self.load_procesos()

    def load_proceso_detalle(self):
        if not self.proceso_id: return
        with rx.session() as session:
            self.proceso_actual = session.get(Proceso, self.proceso_id)
            if self.proceso_actual:
                self.proceso_url_id = self.proceso_actual.codigo_proceso
                if self.proceso_actual.categoria_id:
                    self.categoria_id = str(self.proceso_actual.categoria_id)
                    cat = session.get(Categoria, self.proceso_actual.categoria_id)
                    self.nombre_categoria_actual = cat.nombre if cat else "Desconocida"
                
                ultimo_barrido = session.exec(
                    select(Barrido)
                    .where(Barrido.proceso_id == self.proceso_id)
                    .order_by(desc(Barrido.id))
                ).first()

                if ultimo_barrido:
                    self.barrido_actual_id = ultimo_barrido.id
                    self.ofertas_actuales = session.exec(
                        select(Oferta).where(Oferta.barrido_id == ultimo_barrido.id)
                    ).all()
                    if not self.is_scraping:
                        self.scraping_progress = f"📅 Datos del último barrido ({ultimo_barrido.fecha_fin.strftime('%d/%m %H:%M')})"
                else:
                    self.ofertas_actuales = []
                    self.scraping_progress = "No hay datos previos."

    # --- LÓGICA DE SCRAPING REAL ---
    async def iniciar_scraping(self):
        pid = self.proceso_id
        if not pid or not self.categoria_id:
            self.scraping_progress = "❌ Error: Datos faltantes"
            return
        
        self.is_scraping = True
        self.scraping_progress = "🔄 Preparando entorno..."
        self.ofertas_actuales = [] 
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
        
        # 3. EJECUCIÓN DEL SCRAPER
        total = len(proveedores)
        exitosos = 0
        sin_datos = 0
        
        for i, proveedor in enumerate(proveedores, 1):
            self.scraping_progress = f"🔍 Analizando {i}/{total}: {proveedor.ruc}..."
            yield
            
            try:
                # LLAMADA REAL AL SCRAPER
                datos = await scrape_proceso(self.proceso_url_id, proveedor.ruc)
                
                with rx.session() as session:
                    if datos:
                        exitosos += 1
                        oferta = Oferta(
                            barrido_id=barrido_id,
                            ruc_proveedor=proveedor.ruc,
                            razon_social=datos.get('razon_social', proveedor.nombre),
                            correo_electronico=datos.get('correo_electronico', ''),
                            telefono=datos.get('telefono', ''),
                            pais=datos.get('pais', ''),
                            provincia=datos.get('provincia', ''),
                            canton=datos.get('canton', ''),
                            direccion=datos.get('direccion', ''),
                            descripcion_producto=datos.get('descripcion_producto', ''),
                            unidad=datos.get('unidad', ''),
                            cantidad=datos.get('cantidad', 0.0),
                            valor_unitario=datos.get('valor_unitario', 0.0),
                            valor_total=datos.get('valor_total', 0.0),
                            tiene_archivos=datos.get('tiene_archivos', False),
                            estado="procesado",
                            fecha_scraping=datetime.now()
                        )
                    else:
                        sin_datos += 1
                        oferta = Oferta(
                            barrido_id=barrido_id,
                            ruc_proveedor=proveedor.ruc,
                            razon_social=proveedor.nombre or "",
                            estado="sin_datos",
                            fecha_scraping=datetime.now()
                        )
                    
                    session.add(oferta)
                    session.commit()
                    
                    # Actualizar la vista en tiempo real (opcional, consume recursos)
                    # self.ofertas_actuales.append(oferta) 
            
            except Exception as e:
                print(f"Error procesando {proveedor.ruc}: {e}")
                # Registrar el error como oferta fallida si quieres constancia
        
        # 4. Finalizar
        with rx.session() as session:
             b = session.get(Barrido, barrido_id)
             b.estado = "completado"
             b.fecha_fin = datetime.now()
             b.total_proveedores = total
             b.exitosos = exitosos
             b.sin_datos = sin_datos
             session.commit()

        self.scraping_progress = f"✅ Completado: {exitosos} ofertas encontradas."
        self.is_scraping = False
        
        # 5. Recargar todo para mostrar resultados finales
        self.load_proceso_detalle()