import reflex as rx
from ..states.procesos import ProcesosState

def render_anexos(ruc: str):
    # Filtramos anexos por proveedor
    return rx.vstack(
        rx.text("Documentos Anexos:", font_weight="bold", size="2"),
        rx.foreach(
            ProcesosState.anexos_actuales,
            lambda a: rx.cond(a.ruc_proveedor == ruc, rx.badge(rx.icon("file-text", size=16), a.nombre_archivo, color_scheme="blue"))
        ),
        spacing="1"
    )

def oferta_card(ruc: str):
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor: {ruc}", size="4"),
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
        margin_bottom="4"
    )

def proceso_detalle_view():
    # Obtenemos RUCs únicos del barrido para no repetir tarjetas
    rucs_unicos = rx.var("Array.from(new Set(procesos_state.ofertas_actuales.map(o => o.ruc_proveedor)))")
    
    return rx.vstack(
        rx.button("Volver", on_click=ProcesosState.set_current_view("procesos")),
        rx.heading(f"Código: {ProcesosState.proceso_url_id}"),
        rx.button("Iniciar Barrido", on_click=ProcesosState.iniciar_scraping, loading=ProcesosState.is_scraping),
        rx.foreach(rucs_unicos, oferta_card),
        width="100%", padding="4"
    )