import reflex as rx
from ..states.procesos import ProcesosState

def oferta_detalle_card(o: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(f"Proveedor: {o['razon_social']}", size="4"),
                rx.spacer(),
                rx.badge(o["estado"], color_scheme=rx.cond(o["estado"]=="procesado", "green", "gray")),
                width="100%"
            ),
            rx.grid(
                rx.vstack(rx.text(f"RUC: {o['ruc']}", size="2"), rx.text(f"Correo: {o['correo']}", size="2")),
                rx.vstack(rx.text(f"Ubicación: {o['ubicacion']}", size="2"), rx.text(f"Dirección: {o['direccion']}", size="2")),
                columns="2", width="100%"
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Producto"),
                        rx.table.column_header_cell("Und."),
                        rx.table.column_header_cell("Cant."),
                        rx.table.column_header_cell("V. Unit"),
                        rx.table.column_header_cell("Total"),
                        rx.table.column_header_cell("Anexo"),
                    )
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.cell(o["producto"]),
                        rx.table.cell(o["unidad"]),
                        rx.table.cell(o["cantidad"]),
                        rx.table.cell(o["v_unitario"]),
                        rx.table.cell(o["v_total"], weight="bold"),
                        rx.table.cell(rx.cond(o["tiene_archivos"], rx.icon("file-check", color="blue"), "No")),
                    )
                ),
                variant="surface", width="100%"
            ),
            spacing="3", width="100%"
        ),
        margin_bottom="4", width="100%"
    )

def proceso_detalle_view() -> rx.Component:
    return rx.vstack(
        rx.button(rx.icon("arrow-left"), "Volver a Procesos", variant="ghost", on_click=ProcesosState.volver_a_lista),
        rx.card(
            rx.vstack(
                rx.heading("Detalle del Proceso", size="6"),
                rx.text(f"Código: {ProcesosState.proceso_url_id}", font_family="monospace"),
                rx.badge(f"Categoría: {ProcesosState.nombre_categoria_actual}", variant="outline"),
            ), width="100%"
        ),
        rx.card(
            rx.hstack(
                rx.button(rx.cond(ProcesosState.is_scraping, "Procesando...", "▶️ Iniciar Barrido"), 
                          on_click=ProcesosState.iniciar_scraping, disabled=ProcesosState.is_scraping, color_scheme="grass"),
                rx.text(ProcesosState.scraping_progress),
                align_items="center", spacing="4"
            ), width="100%"
        ),
        rx.vstack(rx.foreach(ProcesosState.ofertas_formateadas, oferta_detalle_card), width="100%"),
        padding="4", width="100%", spacing="5"
    )