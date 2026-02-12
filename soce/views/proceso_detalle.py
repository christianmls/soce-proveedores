import reflex as rx
from ..states.procesos import ProcesosState

def oferta_card(ruc: str):
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor RUC: {ruc}", size="4"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("No."), rx.table.column_header_cell("Descripción"),
                        rx.table.column_header_cell("Unid."), rx.table.column_header_cell("Cant."),
                        rx.table.column_header_cell("V. Unit"), rx.table.column_header_cell("Total")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.ofertas_actuales,
                        lambda o: rx.cond(
                            o.ruc_proveedor == ruc,
                            rx.table.row(
                                rx.table.cell(o.numero_item), rx.table.cell(o.descripcion_producto),
                                rx.table.cell(o.unidad), rx.table.cell(o.cantidad),
                                rx.table.cell(o.valor_unitario), rx.table.cell(o.valor_total)
                            )
                        )
                    )
                )
            ),
            rx.text("Documentos Anexos:", weight="bold", size="2"),
            rx.hstack(
                rx.foreach(
                    ProcesosState.anexos_actuales,
                    lambda a: rx.cond(
                        a.ruc_proveedor == ruc, 
                        rx.link(rx.badge(rx.icon("download", size=14), a.nombre_archivo, color_scheme="blue", cursor="pointer"), href=a.url_archivo, is_external=True)
                    )
                ),
                wrap="wrap"
            ),
            width="100%", spacing="2"
        ),
        margin_bottom="4"
    )

def proceso_detalle_view():
    return rx.vstack(
        rx.button("Volver", on_click=lambda: ProcesosState.set_current_view("procesos"), variant="ghost"),
        rx.card(
            rx.vstack(
                rx.heading(f"Detalle Proceso: {ProcesosState.proceso_url_id}", size="5"),
                rx.hstack(
                    rx.button(rx.cond(ProcesosState.is_scraping, rx.spinner(size="1"), "▶️ Iniciar Barrido"), 
                              on_click=ProcesosState.iniciar_scraping, disabled=ProcesosState.is_scraping, color_scheme="grass"),
                    rx.text(ProcesosState.scraping_progress, weight="bold"),
                    spacing="4"
                )
            ), width="100%"
        ),
        rx.foreach(ProcesosState.rucs_unicos, oferta_card),
        width="100%", padding="4", spacing="4"
    )