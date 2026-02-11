import reflex as rx
from ..states.procesos import ProcesosState

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
                        placeholder="Pegue la URL del SOCE aquí...",
                        on_change=ProcesosState.set_proceso_url_id,
                        value=ProcesosState.proceso_url_id,
                        width="100%"
                    ),
                    rx.text("Parámetros adicionales", size="2", weight="bold", margin_top="4"),
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
                    ),
                    rx.button(
                        "Iniciar Scraping",
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
                        rx.text(ProcesosState.scraping_progress),
                        padding="4",
                        background_color="gray.2",
                        border_radius="md",
                        min_height="200px",
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
        
        # Tabla de resultados
        rx.heading("Resultados del último barrido", size="6", margin_top="6"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("RUC Proveedor"),
                    rx.table.column_header_cell("Objeto del Proceso"),
                    rx.table.column_header_cell("Valor Adjudicado"),
                )
            ),
            rx.table.body(
                rx.foreach(
                    ProcesosState.procesos,
                    lambda p: rx.table.row(
                        rx.table.cell(p.ruc_proveedor),
                        rx.table.cell(p.objeto_proceso),
                        rx.table.cell(f"${p.valor_adjudicado:.2f}" if p.valor_adjudicado else "-"),
                    )
                )
            ),
            width="100%",
            variant="surface"
        ),
        
        spacing="5",
        width="100%",
        padding="4",
        on_mount=ProcesosState.load_categorias,
    )