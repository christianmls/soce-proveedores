import reflex as rx
from ..states.procesos import ProcesosState

def proveedor_detalle_card(proceso) -> rx.Component:
    """Componente para mostrar el detalle de cada proveedor"""
    return rx.card(
        rx.vstack(
            # Header con datos del proveedor
            rx.heading("Datos del Proveedor", size="4", margin_bottom="3"),
            rx.grid(
                rx.vstack(
                    rx.hstack(rx.icon("user"), rx.text("RUC:", weight="bold"), rx.text(proceso.ruc_proveedor), spacing="2"),
                    rx.hstack(rx.icon("building"), rx.text("Razón Social:", weight="bold"), rx.text(proceso.razon_social), spacing="2"),
                    rx.hstack(rx.icon("mail"), rx.text("Correo electrónico:", weight="bold"), rx.text(proceso.correo_electronico), spacing="2"),
                    rx.hstack(rx.icon("phone"), rx.text("Teléfono:", weight="bold"), rx.text(proceso.telefono), spacing="2"),
                    spacing="2",
                    align_items="start",
                ),
                rx.vstack(
                    rx.hstack(rx.icon("flag"), rx.text("País:", weight="bold"), rx.text(proceso.pais), spacing="2"),
                    rx.hstack(rx.icon("map-pin"), rx.text("Provincia:", weight="bold"), rx.text(proceso.provincia), spacing="2"),
                    rx.hstack(rx.icon("map"), rx.text("Cantón:", weight="bold"), rx.text(proceso.canton), spacing="2"),
                    rx.hstack(rx.icon("home"), rx.text("Dirección:", weight="bold"), rx.text(proceso.direccion), spacing="2"),
                    spacing="2",
                    align_items="start",
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),
            
            # Tabla de productos
            rx.divider(margin_y="4"),
            rx.heading("Descripción del Producto", size="4", margin_bottom="3"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Descripción del Producto"),
                        rx.table.column_header_cell("Unidad"),
                        rx.table.column_header_cell("Cantidad"),
                        rx.table.column_header_cell("Valor Unitario Ofertado"),
                        rx.table.column_header_cell("Valor Total"),
                    )
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.cell(proceso.descripcion_producto),
                        rx.table.cell(proceso.unidad),
                        rx.table.cell(f"{proceso.cantidad:.2f}"),
                        rx.table.cell(f"{proceso.valor_unitario:,.2f}"),
                        rx.table.cell(f"{proceso.valor_total:,.5f}"),
                    ),
                    rx.table.row(
                        rx.table.cell("", colspan=4, text_align="right", weight="bold"),
                        rx.table.cell(
                            rx.hstack(
                                rx.text("TOTAL:", weight="bold"),
                                rx.text(f"{proceso.valor_total:,.5f}", weight="bold"),
                                rx.text("USD.", weight="bold"),
                                spacing="2",
                                justify="end",
                            )
                        ),
                    ),
                ),
                variant="surface",
                width="100%",
            ),
            
            # Archivos (si existen)
            rx.cond(
                proceso.tiene_archivos,
                rx.vstack(
                    rx.divider(margin_y="4"),
                    rx.heading("Archivos", size="4"),
                    rx.text("Este proveedor tiene archivos adjuntos", color_scheme="blue"),
                    spacing="2",
                ),
                rx.box()
            ),
            
            spacing="4",
            width="100%",
        ),
        margin_bottom="4",
    )

def procesos_view() -> rx.Component:
    return rx.vstack(
        rx.heading("Barrido de Procesos", size="8"),
        rx.text("Configuración y monitoreo del scraper", color_scheme="gray"),
        
        rx.hstack(
            # Panel de configuración
            rx.card(
                rx.vstack(
                    rx.heading("URL del Proceso", size="5"),
                    rx.input(
                        placeholder="ID del proceso (ej: xrMof7bBhVxPzYlOopcMAsfszTSadIfpeUCMp99edjs)",
                        on_change=ProcesosState.set_proceso_url_id,
                        value=ProcesosState.proceso_url_id,
                        width="100%"
                    ),
                    rx.text("Categoría de Proveedores", size="2", weight="bold", margin_top="4"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Seleccionar Categoría..."),
                        rx.select.content(
                            rx.foreach(
                                ProcesosState.categorias,
                                lambda c: rx.select.item(c.nombre, value=c.id.to_string())
                            )
                        ),
                        on_change=ProcesosState.set_categoria_id,
                        value=ProcesosState.categoria_id,
                        width="100%",
                    ),
                    rx.button(
                        rx.cond(
                            ProcesosState.is_scraping,
                            "⏳ Procesando...",
                            "▶️ Iniciar Scraping"
                        ),
                        on_click=ProcesosState.iniciar_scraping,
                        color_scheme="grass",
                        size="3",
                        disabled=ProcesosState.is_scraping,
                        width="100%",
                        margin_top="4"
                    ),
                    spacing="3",
                    width="100%"
                ),
                width="50%"
            ),
            
            # Consola de actividad
            rx.card(
                rx.vstack(
                    rx.heading("Consola de Actividad", size="5"),
                    rx.box(
                        rx.text(
                            ProcesosState.scraping_progress,
                            white_space="pre-wrap"
                        ),
                        padding="4",
                        background_color="gray.2",
                        border_radius="md",
                        min_height="200px",
                        max_height="400px",
                        overflow_y="auto",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),
        
        # Resultados del barrido con detalles completos
        rx.heading("Resultados del último barrido", size="6", margin_top="6"),
        
        rx.foreach(
            ProcesosState.procesos,
            lambda p: rx.cond(
                p.estado == "procesado",
                proveedor_detalle_card(p),
                rx.box()  # No mostrar los que no tienen datos
            )
        ),
        
        spacing="5",
        width="100%",
        padding="4",
        on_mount=ProcesosState.load_categorias,
    )