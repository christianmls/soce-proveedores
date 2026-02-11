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
    scraping_progress: str = ""
    
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

    def load_procesos(self):
        """Carga los procesos guardados"""
        with rx.session() as session:
            self.procesos = session.exec(Proceso.select()).all()

    async def iniciar_scraping(self):
        """Inicia el proceso de scraping"""
        if not self.proceso_url_id or not self.categoria_id:
            return rx.window_alert("Debes completar el ID del proceso y seleccionar una categoría")
        
        self.is_scraping = True
        self.scraping_progress = "Iniciando scraping..."
        
        # Obtener proveedores de la categoría seleccionada
        with rx.session() as session:
            proveedores = session.exec(
                Proveedor.select().where(
                    Proveedor.categoria_id == int(self.categoria_id)
                )
            ).all()
        
        if not proveedores:
            self.scraping_progress = "No hay proveedores en la categoría seleccionada"
            self.is_scraping = False
            return
        
        self.scraping_progress = f"Encontrados {len(proveedores)} proveedores. Iniciando barrido..."
        
        # Ejecutar scraping para cada proveedor
        from ..utils.scraper import scrape_proceso
        
        for idx, proveedor in enumerate(proveedores, 1):
            self.scraping_progress = f"Procesando {idx}/{len(proveedores)}: {proveedor.nombre or proveedor.ruc}"
            
            try:
                # Llamar a la función de scraping
                datos = await scrape_proceso(self.proceso_url_id, proveedor.ruc)
                
                if datos:
                    # Guardar en la base de datos
                    with rx.session() as session:
                        proceso = Proceso(
                            proceso_id=self.proceso_url_id,
                            ruc_proveedor=proveedor.ruc,
                            nombre_proveedor=datos.get("nombre_proveedor", proveedor.nombre),
                            objeto_proceso=datos.get("objeto", ""),
                            valor_adjudicado=datos.get("valor_total", 0.0),
                            estado="procesado",
                            datos_json=str(datos)
                        )
                        session.add(proceso)
                        session.commit()
                else:
                    # Marcar como sin datos
                    with rx.session() as session:
                        proceso = Proceso(
                            proceso_id=self.proceso_url_id,
                            ruc_proveedor=proveedor.ruc,
                            nombre_proveedor=proveedor.nombre or "",
                            estado="sin_datos"
                        )
                        session.add(proceso)
                        session.commit()
                        
            except Exception as e:
                # Guardar error
                with rx.session() as session:
                    proceso = Proceso(
                        proceso_id=self.proceso_url_id,
                        ruc_proveedor=proveedor.ruc,
                        nombre_proveedor=proveedor.nombre or "",
                        estado="error",
                        datos_json=str(e)
                    )
                    session.add(proceso)
                    session.commit()
            
            # Pequeña pausa entre requests
            await asyncio.sleep(2)
        
        self.scraping_progress = f"✓ Barrido completado: {len(proveedores)} proveedores procesados"
        self.is_scraping = False
        self.load_procesos()