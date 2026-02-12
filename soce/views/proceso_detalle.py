import reflex as rx
from ..states.procesos import ProcesosState

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
            rx.text("Anexos:", weight="bold"),
            rx.foreach(
                ProcesosState.anexos_actuales,
                lambda a: rx.cond(a.ruc_proveedor == ruc, rx.badge(a.nombre_archivo, color_scheme="blue", margin="1"))
            ),
            width="100%", spacing="2"
        )
    )

def proceso_detalle_view():
    return rx.vstack(
        rx.button("Volver", on_click=lambda: ProcesosState.set_current_view("procesos")),
        rx.card(
            rx.vstack(
                rx.heading(f"Proceso: {ProcesosState.proceso_url_id}"),
                rx.button(
                    rx.cond(ProcesosState.is_scraping, rx.spinner(size="1"), "Iniciar Barrido"),
                    on_click=ProcesosState.iniciar_scraping,
                    disabled=ProcesosState.is_scraping
                ),
                rx.text(ProcesosState.scraping_progress)
            )
        ),
        rx.foreach(ProcesosState.rucs_unicos, oferta_card),
        width="100%", padding="4"
    )