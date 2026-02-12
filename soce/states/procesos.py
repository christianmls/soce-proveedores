import reflex as rx
from typing import Optional
from ..models import Proceso, Proveedor, Categoria
from ..state import State
import asyncio
from datetime import datetime

class ProcesosState(State):
    # Datos de configuración
    proceso_url_id: str = ""
    categoria_id: str = ""
    
    # Control del scraping
    is_scraping: bool = False
    scraping_progress: str = "Esperando configuración..."
    
    # Datos
    categorias: list[Categoria] = []
    procesos: list[Proceso] = []
    
    def set_proceso_url_id(self, val: str):
        self.proceso_url_id = val
    
    def set_categoria_id(self, val: str):
        self.categoria_id = val

    def load_categorias(self):
        """Carga todas las categorías disponibles"""
        with rx.session() as session:
            self.categorias = session.exec(Categoria.select()).all()
        self.scraping_progress = "Listo para iniciar"

    def load_procesos(self):
        """Carga los procesos guardados"""
        with rx.session() as session:
            self.procesos = session.exec(Proceso.select()).all()

    async def iniciar_scraping(self):
        """Inicia el proceso de scraping"""
        if not self.proceso_url_id:
            self.scraping_progress = "❌ Error: Debes ingresar el ID del proceso"
            return
            
        if not self.categoria_id:
            self.scraping_progress = "❌ Error: Debes seleccionar una categoría"
            return
        
        self.is_scraping = True
        self.scraping_progress = "🔄 Iniciando scraping..."
        yield
        
        # Obtener proveedores de la categoría seleccionada
        with rx.session() as session:
            proveedores = session.exec(
                Proveedor.select().where(
                    Proveedor.categoria_id == int(self.categoria_id)
                )
            ).all()
        
        if not proveedores:
            self.scraping_progress = "⚠️ No hay proveedores en la categoría seleccionada"
            self.is_scraping = False
            yield
            return
        
        self.scraping_progress = f"📋 Encontrados {len(proveedores)} proveedores. Iniciando barrido..."
        yield
        
        # Importar función de scraping
        from ..utils.scraper import scrape_proceso
        
        # Procesar cada proveedor
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
                    # Guardar en la base de datos con todos los campos
                    with rx.session() as session:
                        proceso = Proceso(
                            proceso_id=self.proceso_url_id,
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
                            fecha_barrido=datetime.now(),
                            estado="procesado",
                            tiene_archivos=datos.get('tiene_archivos', False),
                            datos_completos_json=str(datos)
                        )
                        session.add(proceso)
                        session.commit()
                    
                    exitosos += 1
                    self.scraping_progress = f"✅ {idx}/{total}: Datos completos para {datos.get('razon_social', proveedor.ruc)}"
                else:
                    # Marcar como sin datos
                    with rx.session() as session:
                        proceso = Proceso(
                            proceso_id=self.proceso_url_id,
                            ruc_proveedor=proveedor.ruc,
                            razon_social=proveedor.nombre or "",
                            fecha_barrido=datetime.now(),
                            estado="sin_datos"
                        )
                        session.add(proceso)
                        session.commit()
                    
                    sin_datos += 1
                    self.scraping_progress = f"⚪ {idx}/{total}: Sin datos para {proveedor.ruc}"
                
                yield
                        
            except Exception as e:
                # Guardar error
                with rx.session() as session:
                    proceso = Proceso(
                        proceso_id=self.proceso_url_id,
                        ruc_proveedor=proveedor.ruc,
                        razon_social=proveedor.nombre or "",
                        fecha_barrido=datetime.now(),
                        estado="error",
                        datos_completos_json=str(e)
                    )
                    session.add(proceso)
                    session.commit()
                
                errores += 1
                self.scraping_progress = f"❌ {idx}/{total}: Error en {proveedor.ruc} - {str(e)}"
                yield
            
            # Pequeña pausa entre requests para no sobrecargar el servidor
            await asyncio.sleep(2)
        
        # Resumen final
        self.scraping_progress = f"✅ Completado! Exitosos: {exitosos} | Sin datos: {sin_datos} | Errores: {errores}"
        self.is_scraping = False
        self.load_procesos()
        yield