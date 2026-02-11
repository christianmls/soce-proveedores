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
    is_scraping: bool = False  # Asegúrate que esté en False inicialmente
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
                datos = await scrape_proceso(self.proceso_url_id, proveedor.ruc)
                
                if datos:
                    with rx.session() as session:
                        proceso = Proceso(
                            proceso_id=self.proceso_url_id,
                            ruc_proveedor=proveedor.ruc,
                            nombre_proveedor=datos.get("nombre_proveedor", proveedor.nombre or ""),
                            objeto_proceso=datos.get("objeto", ""),
                            valor_adjudicado=datos.get("valor_total", 0.0),
                            fecha_barrido=datetime.now(),
                            estado="procesado",
                            datos_json=str(datos)
                        )
                        session.add(proceso)
                        session.commit()
                    exitosos += 1
                else:
                    with rx.session() as session:
                        proceso = Proceso(
                            proceso_id=self.proceso_url_id,
                            ruc_proveedor=proveedor.ruc,
                            nombre_proveedor=proveedor.nombre or "",
                            fecha_barrido=datetime.now(),
                            estado="sin_datos"
                        )
                        session.add(proceso)
                        session.commit()
                    sin_datos += 1
                
                yield
                        
            except Exception as e:
                with rx.session() as session:
                    proceso = Proceso(
                        proceso_id=self.proceso_url_id,
                        ruc_proveedor=proveedor.ruc,
                        nombre_proveedor=proveedor.nombre or "",
                        fecha_barrido=datetime.now(),
                        estado="error",
                        datos_json=str(e)
                    )
                    session.add(proceso)
                    session.commit()
                errores += 1
                yield
            
            await asyncio.sleep(1)
        
        self.scraping_progress = f"✅ Completado! Exitosos: {exitosos} | Sin datos: {sin_datos} | Errores: {errores}"
        self.is_scraping = False
        self.load_procesos()
        yield