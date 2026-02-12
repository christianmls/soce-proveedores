import reflex as rx
from ..states.procesos import ProcesosState

def procesos_view() -> rx.Component:
    return rx.vstack(
        rx.heading("Procesos de Contratación", size="8"),
        rx.text("Gestión de procesos y barridos", color_scheme="gray"),
        
        # Botón Nuevo simplificado
        rx.dialog.root(
            rx.dialog.trigger(rx.button(rx.icon("plus"), "Nuevo Proceso", color_scheme="grass")),
            rx.dialog.content(
                rx.dialog.title("Crear Nuevo Proceso"),
                rx.vstack(
                    rx.input(placeholder="Código", on_change=ProcesosState.set_nuevo_codigo_proceso),
                    rx.input(placeholder="Nombre (opcional)", on_change=ProcesosState.set_nuevo_nombre_proceso),
                    rx.dialog.close(rx.button("Guardar", on_click=ProcesosState.crear_proceso)),
                )
            )
        ),
        
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("ID"),
                    rx.table.column_header_cell("Código"),
                    rx.table.column_header_cell("Nombre"),
                    rx.table.column_header_cell("Fecha"),
                    rx.table.column_header_cell("Acción"),
                )
            ),
            rx.table.body(
                rx.foreach(
                    ProcesosState.lista_procesos_formateada,
                    lambda p: rx.table.row(
                        rx.table.cell(p["id"]),
                        rx.table.cell(rx.text(p["codigo_corto"], font_family="monospace")),
                        rx.table.cell(p["nombre"]),
                        rx.table.cell(p["fecha"]),
                        rx.table.cell(
                            rx.link(
                                rx.button(rx.icon("eye"), size="1", variant="soft"),
                                href=f"/proceso/{p['id']}"
                            )
                        ),
                    )
                )
            ),
            width="100%",
        ),
        on_mount=ProcesosState.load_procesos,
        spacing="5", padding="4", width="100%"
    )