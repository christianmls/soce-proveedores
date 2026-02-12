import reflex as rx
from ..states.procesos import ProcesosState

def oferta_detalle_card(o: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor: {o['razon_social']}", size="4"),
            rx.grid(
                rx.text(f"RUC: {o['ruc']}"),
                rx.text(f"Ubicación: {o['ubicacion']}"),
                columns="2", width="100%"
            ),
            rx.table.root(
                rx.table.body(
                    rx.table.row(
                        rx.table.cell(o["producto"]),
                        rx.table.cell(o["v_unitario"]),
                        rx.table.cell(o["v_total"], weight="bold"),
                    )
                ),
                width="100%"
            ),
        ),
        margin_bottom="4"
    )

def proceso_detalle_view() -> rx.Component:
    return rx.vstack(
        rx.link(rx.button(rx.icon("arrow-left"), "Volver"), href="/procesos"),
        
        # Historial de Barridos
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("ID"),
                    rx.table.column_header_cell("Estado"),
                    rx.table.column_header_cell("Acción")
                )
            ),
            rx.table.body(
                rx.foreach(
                    ProcesosState.barridos_formateados,
                    lambda b: rx.table.row(
                        rx.table.cell(b["id"]),
                        rx.table.cell(rx.badge(b["estado"])),
                        rx.table.cell(
                            rx.button(
                                "Ver Ofertas", 
                                # CORRECCIÓN: Usar lambda para no ejecutar la función al renderizar
                                on_click=lambda: ProcesosState.set_barrido_seleccionado(b["id"])
                            )
                        )
                    )
                )
            ),
            width="100%"
        ),

        # Sección de Ofertas
        rx.cond(
            ProcesosState.barrido_seleccionado_id,
            rx.vstack(
                rx.heading("Ofertas del Barrido", size="5"),
                rx.foreach(ProcesosState.ofertas_formateadas, oferta_detalle_card),
                width="100%"
            )
        ),
        on_mount=ProcesosState.load_proceso_detalle,
        padding="4", width="100%", spacing="5"
    )