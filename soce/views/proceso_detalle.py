import reflex as rx
from ..states.procesos import ProcesosState

def oferta_detalle_card(o: dict) -> rx.Component:
    """Tarjeta de diseño para mostrar una oferta individual"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(f"Proveedor: {o['razon_social']}", size="4"),
                rx.spacer(),
                rx.badge(o["estado"], color_scheme=rx.cond(o["estado"]=="procesado", "green", "gray")),
                width="100%"
            ),
            rx.grid(
                rx.vstack(
                    rx.text(f"RUC: {o['ruc']}", size="2", color_scheme="gray"),
                    rx.text(f"Correo: {o['correo']}", size="2", color_scheme="gray"),
                ),
                rx.vstack(
                    rx.text(f"Ubicación: {o['ubicacion']}", size="2", color_scheme="gray"),
                    rx.text(f"Dirección: {o['direccion']}", size="2", color_scheme="gray"),
                ),
                columns="2", width="100%"
            ),
            rx.divider(margin_y="2"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Producto"),
                        rx.table.column_header_cell("Cant."),
                        rx.table.column_header_cell("V. Unit"),
                        rx.table.column_header_cell("Total"),
                    )
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.cell(o["producto"]),
                        rx.table.cell(o["cantidad"]),
                        rx.table.cell(o["v_unitario"]),
                        rx.table.cell(o["v_total"], weight="bold"),
                    )
                ),
                variant="surface", width="100%"
            ),
            spacing="3",
            width="100%"
        ),
        margin_bottom="4",
        width="100%"
    )

def proceso_detalle_view() -> rx.Component:
    return rx.vstack(
        # Botón Volver
        rx.button(
            rx.icon("arrow-left"), 
            "Volver a Procesos", 
            variant="ghost", 
            on_click=ProcesosState.volver_a_lista
        ),
        
        # Header del Proceso
        rx.card(
            rx.vstack(
                rx.heading("Detalle del Proceso", size="6"),
                rx.text(f"Código: {ProcesosState.proceso_url_id}", font_family="monospace"),
                # Mostramos la categoría asociada (Read Only)
                rx.hstack(
                    rx.badge("Categoría:", variant="outline"),
                    rx.text(ProcesosState.nombre_categoria_actual, weight="bold"),
                    align_items="center"
                )
            ),
            width="100%"
        ),

        # Barra de Acción (Botón Iniciar + Estado)
        rx.card(
            rx.hstack(
                rx.button(
                    rx.cond(ProcesosState.is_scraping, "Procesando...", "▶️ Iniciar Barrido"), 
                    on_click=ProcesosState.iniciar_scraping, 
                    disabled=ProcesosState.is_scraping, 
                    color_scheme="grass",
                    size="3"
                ),
                rx.text(ProcesosState.scraping_progress, weight="medium", color_scheme="gray"),
                align_items="center", spacing="4"
            ),
            width="100%"
        ),

        rx.divider(),
        
        # Título dinámico
        rx.heading(
            rx.cond(
                ProcesosState.tiene_ofertas,
                "Resultados del Último Barrido",
                "No hay ofertas para mostrar. Inicia un barrido."
            ), 
            size="5"
        ),

        # --- CONTENEDOR DE OFERTAS (DIRECTO) ---
        rx.vstack(
            rx.foreach(
                ProcesosState.ofertas_formateadas,
                oferta_detalle_card
            ),
            width="100%",
            spacing="4"
        ),
        
        padding="4", width="100%", spacing="5"
    )