import reflex as rx
from ..states.procesos import ProcesosState

def oferta_card(resumen: rx.Var):
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor RUC: {resumen['ruc']}", size="4", color_scheme="grass"),
            rx.table.root(
                rx.table.header(rx.table.row(rx.table.column_header_cell("No."), rx.table.column_header_cell("Descripción"), rx.table.column_header_cell("Total"))),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.ofertas_actuales,
                        lambda o: rx.cond(
                            o.ruc_proveedor == resumen['ruc'],
                            rx.table.row(rx.table.cell(o.numero_item), rx.table.cell(o.descripcion_producto), rx.table.cell(o.valor_total))
                        )
                    ),
                    # Muestra el total pre-calculado por el Backend
                    rx.table.row(
                        rx.table.cell(""), rx.table.cell("TOTAL PROFORMA", weight="bold"),
                        rx.table.cell(resumen['total'], weight="bold", color="green")
                    )
                ),
                width="100%"
            ),
            rx.vstack(
                rx.text("Anexos:", weight="bold"),
                rx.flex(rx.foreach(ProcesosState.anexos_actuales, lambda a: rx.cond(a.ruc_proveedor == resumen['ruc'], rx.link(rx.badge(a.nombre_archivo), href=a.url_archivo, is_external=True))), wrap="wrap", spacing="2"),
                width="100%"
            ),
            width="100%", spacing="3"
        ),
        width="100%", margin_bottom="4"
    )

def proceso_detalle_view():
    return rx.vstack(
        rx.button("Volver", on_click=lambda: ProcesosState.set_current_view("procesos")),
        rx.card(rx.hstack(rx.button(rx.cond(ProcesosState.is_scraping, rx.spinner(size="1"), "Iniciar Barrido"), on_click=ProcesosState.iniciar_scraping, disabled=ProcesosState.is_scraping), rx.text(ProcesosState.scraping_progress), width="100%", justify="between"), width="100%"),
        rx.foreach(ProcesosState.resumen_proveedores, oferta_card), # Usa el rx.Var correcto
        width="100%", padding="4", align_items="stretch"
    )