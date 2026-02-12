import reflex as rx
from ..states.procesos import ProcesosState

def procesos_view():
    return rx.vstack(
        rx.heading("Procesos de Contratación"),
        rx.dialog.root(
            rx.dialog.trigger(rx.button(rx.icon("plus"), "Nuevo Proceso", color_scheme="grass")),
            rx.dialog.content(
                rx.vstack(
                    rx.input(placeholder="Código", on_change=ProcesosState.set_nuevo_codigo_proceso),
                    rx.input(placeholder="Nombre", on_change=ProcesosState.set_nuevo_nombre_proceso),
                    rx.select.root(
                        rx.select.trigger(placeholder="Categoría"),
                        rx.select.content(rx.foreach(ProcesosState.categorias, lambda c: rx.select.item(c.nombre, value=c.id.to_string()))),
                        on_change=ProcesosState.set_categoria_id
                    ),
                    rx.dialog.close(rx.button("Guardar", on_click=ProcesosState.crear_proceso, color_scheme="grass")),
                )
            )
        ),
        rx.table.root(
            rx.table.header(rx.table.row(rx.table.column_header_cell("Código"), rx.table.column_header_cell("Acciones"))),
            rx.table.body(rx.foreach(ProcesosState.lista_procesos_formateada, lambda p: rx.table.row(
                rx.table.cell(p["codigo"]),
                rx.table.cell(rx.hstack(
                    rx.button(rx.icon("eye"), on_click=lambda: ProcesosState.ir_a_detalle(p["id"]), size="1"),
                    rx.button(rx.icon("trash-2"), on_click=lambda: ProcesosState.eliminar_proceso(p["id"]), size="1", color_scheme="red")
                ))
            ))),
            width="100%"
        ),
        on_mount=ProcesosState.load_procesos, width="100%", spacing="5"
    )