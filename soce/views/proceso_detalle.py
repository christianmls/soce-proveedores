import reflex as rx
from ..states.procesos import ProcesosState

def oferta_detalle_card(o: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor: {o['razon_social']}", size="4"),
            rx.grid(
                rx.vstack(rx.text(f"RUC: {o['ruc']}"), rx.text(f"Correo: {o['correo']}")),
                rx.vstack(rx.text(f"Ubicación: {o['ubicacion']}"), rx.text(f"Dirección: {o['direccion']}")),
                columns="2", width="100%"
            ),
            rx.divider(),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Producto"),
                        rx.table.column_header_cell("Cant."),
                        rx.table.column_header_cell("V. Unit"),
                        rx.table.column_header_cell("Total"),
                    )
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.cell(o["producto"]),
                        rx.table.cell(o["cantidad"]),
                        rx.table.cell(o["v_unitario"]),
                        rx.table.cell(o["v_total"], weight="bold"),
                    )
                ),
                variant="surface", width="100%"
            ),
            spacing="3"
        ),
        margin_bottom="4"
    )

def proceso_detalle_view() -> rx.Component:
    return rx.vstack(
        # CAMBIO CLAVE: Botón volver usa estado, no href
        rx.button(
            rx.icon("arrow-left"), 
            "Volver a Procesos", 
            variant="ghost", 
            on_click=ProcesosState.volver_a_lista
        ),
        
        rx.card(
            rx.vstack(
                rx.heading("Detalle del Proceso", size="6"),
                rx.text(f"Código: {ProcesosState.proceso_url_id}", font_family="monospace"),
            ),
            width="100%"
        ),

        rx.card(
            rx.hstack(
                rx.select.root(
                    rx.select.trigger(placeholder="Seleccionar Categoría..."),
                    rx.select.content(
                        rx.foreach(ProcesosState.categorias, lambda c: rx.select.item(c.nombre, value=c.id.to_string()))
                    ),
                    on_change=ProcesosState.set_categoria_id,
                    value=ProcesosState.categoria_id,
                ),
                rx.button("Iniciar Barrido", on_click=ProcesosState.iniciar_scraping, disabled=ProcesosState.is_scraping, color_scheme="grass"),
                rx.text(ProcesosState.scraping_progress),
                align_items="center", spacing="4"
            ),
            width="100%"
        ),

        rx.heading("Historial", size="5"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("ID"),
                    rx.table.column_header_cell("Fecha"),
                    rx.table.column_header_cell("Total"),
                    rx.table.column_header_cell("Estado"),
                    rx.table.column_header_cell("Acción")
                )
            ),
            rx.table.body(
                rx.foreach(
                    ProcesosState.barridos_formateados,
                    lambda b: rx.table.row(
                        rx.table.cell(b["id"]),
                        rx.table.cell(b["fecha_inicio"]),
                        rx.table.cell(b["total"]),
                        rx.table.cell(rx.badge(b["estado"])),
                        rx.table.cell(
                            rx.button("Ver Ofertas", on_click=lambda: ProcesosState.set_barrido_seleccionado(b["id"]), size="1", variant="soft")
                        )
                    )
                )
            ),
            width="100%", variant="surface"
        ),

        rx.cond(
            ProcesosState.barrido_seleccionado_id,
            rx.vstack(
                rx.heading(f"Resultados Barrido #{ProcesosState.barrido_seleccionado_id}", size="5"),
                rx.foreach(ProcesosState.ofertas_formateadas, oferta_detalle_card),
                width="100%"
            )
        ),
        padding="4", width="100%", spacing="5"
    )