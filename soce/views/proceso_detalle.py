import reflex as rx
from ..states.procesos import ProcesosState

def oferta_card(ruc: str):
    # Calculamos el total sumando las filas de este RUC para mostrar el Total General
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor: {ruc}", size="4", color_scheme="grass"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("No."), rx.table.column_header_cell("Descripción Detallada"),
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
                                rx.table.cell(o.numero_item), 
                                rx.table.cell(o.descripcion_producto, size="1"),
                                rx.table.cell(o.unidad), rx.table.cell(o.cantidad),
                                rx.table.cell(o.valor_unitario), rx.table.cell(o.valor_total)
                            )
                        )
                    )
                ),
                variant="surface", width="100%"
            ),
            # Sección de Anexos
            rx.vstack(
                rx.text("Documentos Anexos Detectados:", weight="bold", size="2"),
                rx.flex(
                    rx.foreach(
                        ProcesosState.anexos_actuales,
                        lambda a: rx.cond(
                            a.ruc_proveedor == ruc,
                            rx.badge(
                                rx.icon("file-text", size=14), 
                                a.nombre_archivo, 
                                color_scheme="blue", margin="1"
                            )
                        )
                    ),
                    wrap="wrap"
                ),
                width="100%", align_items="start", spacing="1"
            ),
            width="100%", spacing="3"
        ),
        margin_bottom="4"
    )

def proceso_detalle_view():
    return rx.vstack(
        rx.button("Volver", on_click=lambda: ProcesosState.set_current_view("procesos"), variant="ghost"),
        rx.card(
            rx.vstack(
                rx.heading(f"Proceso: {ProcesosState.proceso_url_id}", size="5"),
                rx.hstack(
                    rx.button(
                        rx.cond(ProcesosState.is_scraping, rx.spinner(size="1"), "▶️ Iniciar Barrido"),
                        on_click=ProcesosState.iniciar_scraping,
                        disabled=ProcesosState.is_scraping,
                        color_scheme="grass"
                    ),
                    rx.text(ProcesosState.scraping_progress, weight="bold"),
                    spacing="4"
                )
            ), width="100%"
        ),
        rx.divider(),
        rx.vstack(
            rx.foreach(ProcesosState.rucs_unicos, oferta_card),
            width="100%"
        ),
        width="100%", padding="4", spacing="4"
    )