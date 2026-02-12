import reflex as rx
from ..states.procesos import ProcesosState

def oferta_card(ruc: str):
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor RUC: {ruc}", size="4", color_scheme="grass"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("No."), rx.table.column_header_cell("Descripción"), 
                        rx.table.column_header_cell("Total")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.ofertas_actuales, 
                        lambda o: rx.cond(
                            o.ruc_proveedor == ruc, 
                            rx.table.row(rx.table.cell(o.numero_item), rx.table.cell(o.descripcion_producto), rx.table.cell(o.valor_total))
                        )
                    )
                ),
                width="100%"
            ),
            rx.vstack(
                rx.text("Documentos Anexos:", weight="bold", size="2"),
                rx.flex(
                    rx.foreach(
                        ProcesosState.anexos_actuales, 
                        lambda a: rx.cond(
                            a.ruc_proveedor == ruc, 
                            rx.link(rx.badge(rx.icon("file-down", size=14), a.nombre_archivo, color_scheme="blue"), href=a.url_archivo, is_external=True)
                        )
                    ), 
                    wrap="wrap", spacing="2"
                ),
                width="100%", align_items="start"
            ),
            width="100%", spacing="3"
        ),
        width="100%", margin_bottom="4"
    )

def proceso_detalle_view():
    return rx.vstack(
        rx.button("Volver", on_click=lambda: ProcesosState.set_current_view("procesos"), variant="ghost"),
        rx.card(
            rx.hstack(
                rx.button(
                    rx.cond(ProcesosState.is_scraping, rx.spinner(size="1"), "▶️ Iniciar Barrido"), 
                    on_click=ProcesosState.iniciar_scraping, disabled=ProcesosState.is_scraping, color_scheme="grass"
                ),
                rx.text(ProcesosState.scraping_progress, weight="bold"),
                width="100%", justify="between"
            ),
            width="100%"
        ),
        rx.vstack(
            rx.foreach(ProcesosState.rucs_unicos, oferta_card),
            width="100%", align_items="stretch"
        ),
        width="100%", padding="4"
    )