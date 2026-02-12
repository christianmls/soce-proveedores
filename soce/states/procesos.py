import reflex as rx
from typing import Optional
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
    
    # ID del proceso actual (para routing)
    proceso_id: Optional[int] = None
    
    def set_proceso_url_id(self, val: str):
        self.proceso_url_id = val
    
    def set_categoria_id(self, val: str):
        self.categoria_id = val
    
    def set_nuevo_codigo_proceso(self, val: str):
        self.nuevo_codigo_proceso = val
    
    def set_nuevo_nombre_proceso(self, val: str):
        self.nuevo_nombre_proceso = val
    
    def set_barrido_seleccionado(self, val: str):
        self.barrido_seleccionado_id = int(val) if val else None
        self.cargar_ofertas_barrido()

    def load_categorias(self):
        """Carga todas las categorías disponibles"""
        with rx.session() as session:
            self.categorias = session.exec(Categoria.select()).all()

    def load_procesos(self):
        """Carga todos los procesos"""
        with rx.session() as session:
            self.procesos = session.exec(Proceso.select()).all()
    
    def crear_proceso(self):
        """Crea un nuevo proceso"""
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
        
        # Limpiar campos
        self.nuevo_codigo_proceso = ""
        self.nuevo_nombre_proceso = ""
        
        # Recargar lista
        self.load_procesos()
    
    def load_proceso_detalle(self):
        """Carga el detalle de un proceso específico"""
        # El proceso_id viene de la URL mediante el router
        if not self.proceso_id:
            return
        
        with rx.session() as session:
            self.proceso_actual = session.get(Proceso, self.proceso_id)
            
            if self.proceso_actual:
                self.proceso_url_id = self.proceso_actual.codigo_proceso
                
                # Cargar barridos de este proceso
                self.barridos = session.exec(
                    Barrido.select().where(Barrido.proceso_id == self.proceso_id)
                ).all()
        
        # Cargar categorías
        self.load_categorias()
    
    def load_barridos(self):
        """Carga todos los barridos del proceso actual"""
        if not self.proceso_id:
            return
        
        with rx.session() as session:
            self.barridos = session.exec(
                Barrido.select().where(Barrido.proceso_id == self.proceso_id)
            ).all()
    
    def cargar_ofertas_barrido(self):
        """Carga las ofertas del barrido seleccionado"""
        if not self.barrido_seleccionado_id:
            self.ofertas_actuales = []
            return
        
        with rx.session() as session:
            self.ofertas_actuales = session.exec(
                Oferta.select().where(Oferta.barrido_id == self.barrido_seleccionado_id)
            ).all()

    async def iniciar_scraping(self):
        """Inicia el proceso de scraping"""
        if not self.proceso_id:
            self.scraping_progress = "❌ Error: No hay proceso seleccionado"
            return
            
        if not self.categoria_id:
            self.scraping_progress = "❌ Error: Debes seleccionar una categoría"
            return
        
        self.is_scraping = True
        self.scraping_progress = "🔄 Iniciando scraping..."
        yield
        
        # 1. Crear un nuevo Barrido
        with rx.session() as session:
            barrido = Barrido(
                proceso_id=self.proceso_id,
                categoria_id=int(self.categoria_id),
                fecha_inicio=datetime.now(),
                estado="en_proceso"
            )
            session.add(barrido)
            session.commit()
            session.refresh(barrido)
            barrido_id = barrido.id
        
        # 2. Obtener proveedores de la categoría
        with rx.session() as session:
            proveedores = session.exec(
                Proveedor.select().where(
                    Proveedor.categoria_id == int(self.categoria_id)
                )
            ).all()
        
        if not proveedores:
            self.scraping_progress = "⚠️ No hay proveedores en la categoría seleccionada"
            with rx.session() as session:
                barrido = session.get(Barrido, barrido_id)
                barrido.estado = "completado"
                barrido.fecha_fin = datetime.now()
                session.commit()
            self.is_scraping = False
            yield
            return
        
        self.scraping_progress = f"📋 Encontrados {len(proveedores)} proveedores. Iniciando barrido..."
        yield
        
        # 3. Actualizar total de proveedores en el barrido
        with rx.session() as session:
            barrido = session.get(Barrido, barrido_id)
            barrido.total_proveedores = len(proveedores)
            session.commit()
        
        # 4. Importar función de scraping
        from ..utils.scraper import scrape_proceso
        
        # 5. Procesar cada proveedor
        total = len(proveedores)
        exitosos = 0
        sin_datos = 0
        errores = 0
        
        for idx, proveedor in enumerate(proveedores, 1):
            self.scraping_progress = f"🔍 Procesando {idx}/{total}: {proveedor.nombre or proveedor.ruc}..."
            yield
            
            try:
                # Llamar a la función de scraping
                datos = await scrape_proceso(self.proceso_url_id, proveedor.ruc)
                
                if datos:
                    # Guardar oferta con datos
                    with rx.session() as session:
                        oferta = Oferta(
                            barrido_id=barrido_id,
                            ruc_proveedor=proveedor.ruc,
                            
                            # Datos del proveedor
                            razon_social=datos.get('razon_social', ''),
                            correo_electronico=datos.get('correo_electronico', ''),
                            telefono=datos.get('telefono', ''),
                            pais=datos.get('pais', ''),
                            provincia=datos.get('provincia', ''),
                            canton=datos.get('canton', ''),
                            direccion=datos.get('direccion', ''),
                            
                            # Datos del producto
                            descripcion_producto=datos.get('descripcion_producto', ''),
                            unidad=datos.get('unidad', ''),
                            cantidad=datos.get('cantidad', 0.0),
                            valor_unitario=datos.get('valor_unitario', 0.0),
                            valor_total=datos.get('valor_total', 0.0),
                            
                            # Metadatos
                            fecha_scraping=datetime.now(),
                            estado="procesado",
                            tiene_archivos=datos.get('tiene_archivos', False),
                            datos_completos_json=str(datos)
                        )
                        session.add(oferta)
                        session.commit()
                    
                    exitosos += 1
                    self.scraping_progress = f"✅ {idx}/{total}: Datos completos para {datos.get('razon_social', proveedor.ruc)}"
                else:
                    # Guardar oferta sin datos
                    with rx.session() as session:
                        oferta = Oferta(
                            barrido_id=barrido_id,
                            ruc_proveedor=proveedor.ruc,
                            razon_social=proveedor.nombre or "",
                            fecha_scraping=datetime.now(),
                            estado="sin_datos"
                        )
                        session.add(oferta)
                        session.commit()
                    
                    sin_datos += 1
                    self.scraping_progress = f"⚪ {idx}/{total}: Sin datos para {proveedor.ruc}"
                
                yield
                        
            except Exception as e:
                # Guardar oferta con error
                with rx.session() as session:
                    oferta = Oferta(
                        barrido_id=barrido_id,
                        ruc_proveedor=proveedor.ruc,
                        razon_social=proveedor.nombre or "",
                        fecha_scraping=datetime.now(),
                        estado="error",
                        datos_completos_json=str(e)
                    )
                    session.add(oferta)
                    session.commit()
                
                errores += 1
                self.scraping_progress = f"❌ {idx}/{total}: Error en {proveedor.ruc}"
                yield
            
            # Pausa entre requests
            await asyncio.sleep(2)
        
        # 6. Finalizar barrido
        with rx.session() as session:
            barrido = session.get(Barrido, barrido_id)
            barrido.estado = "completado"
            barrido.fecha_fin = datetime.now()
            barrido.exitosos = exitosos
            barrido.sin_datos = sin_datos
            barrido.errores = errores
            session.commit()
        
        # 7. Resumen final
        self.scraping_progress = f"✅ Completado! Exitosos: {exitosos} | Sin datos: {sin_datos} | Errores: {errores}"
        self.is_scraping = False
        self.load_barridos()
        self.barrido_seleccionado_id = barrido_id
        self.cargar_ofertas_barrido()
        yield