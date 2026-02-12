import reflex as rx
from ..states.procesos import ProcesosState

def render_anexos(ruc: str):
    return rx.vstack(
        rx.text("Documentos Anexos:", font_weight="bold", size="2", margin_top="2"),
        rx.flex(
            rx.foreach(
                ProcesosState.anexos_actuales,
                lambda a: rx.cond(a.ruc_proveedor == ruc, rx.badge(rx.icon("file-text", size=14), a.nombre_archivo, color_scheme="blue", margin_right="2"))
            ),
            wrap="wrap"
        )
    )

def oferta_card(ruc: str):
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor RUC: {ruc}", size="4"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("No."), rx.table.column_header_cell("CPC"),
                        rx.table.column_header_cell("Descripción"), rx.table.column_header_cell("Cant."),
                        rx.table.column_header_cell("V. Unit"), rx.table.column_header_cell("Total")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.ofertas_actuales,
                        lambda o: rx.cond(
                            o.ruc_proveedor == ruc,
                            rx.table.row(
                                rx.table.cell(o.numero_item), rx.table.cell(o.cpc),
                                rx.table.cell(o.descripcion_producto), rx.table.cell(o.cantidad),
                                rx.table.cell(o.valor_unitario), rx.table.cell(o.valor_total)
                            )
                        )
                    )
                )
            ),
            render_anexos(ruc),
            width="100%", spacing="3"
        ),
        margin_bottom="4", width="100%"
    )

def proceso_detalle_view():
    return rx.vstack(
        rx.button(rx.icon("arrow-left"), "Volver", on_click=lambda: ProcesosState.set_current_view("procesos"), variant="ghost"),
        rx.card(
            rx.vstack(
                rx.heading("Detalle del Proceso", size="6"),
                rx.text(f"Código: {ProcesosState.proceso_url_id}", font_family="monospace"),
                rx.button(
                    rx.cond(ProcesosState.is_scraping, "Procesando...", "▶️ Iniciar Barrido"),
                    on_click=ProcesosState.iniciar_scraping,
                    loading=ProcesosState.is_scraping,
                    color_scheme="grass"
                ),
                rx.text(ProcesosState.scraping_progress, size="2", color_scheme="gray"),
            ), width="100%"
        ),
        rx.vstack(
            rx.foreach(ProcesosState.rucs_unicos, oferta_card),
            width="100%"
        ),
        width="100%", spacing="5", padding="4"
    )