import reflex as rx
from ..states.procesos import ProcesosState

def procesos_view() -> rx.Component:
    """Vista principal: Lista de procesos"""
    return rx.vstack(
        rx.heading("Procesos de Contratación", size="8"),
        rx.text("Gestión de procesos y barridos", color_scheme="gray"),
        
        # Botón para crear nuevo proceso
        rx.hstack(
            rx.spacer(),
            rx.dialog.root(
                rx.dialog.trigger(
                    rx.button(
                        rx.icon("plus"),
                        "Nuevo Proceso",
                        color_scheme="grass",
                        size="3"
                    )
                ),
                rx.dialog.content(
                    rx.dialog.title("Crear Nuevo Proceso"),
                    rx.vstack(
                        rx.text("ID del Proceso", size="2", weight="bold"),
                        rx.input(
                            placeholder="ej: xrMof7bBhVxPzYlOopcMAsfszTSadIfpeUCMp99edjs",
                            on_change=ProcesosState.set_nuevo_codigo_proceso,
                            value=ProcesosState.nuevo_codigo_proceso,
                            width="100%"
                        ),
                        rx.text("Nombre del Proceso (opcional)", size="2", weight="bold", margin_top="3"),
                        rx.input(
                            placeholder="Nombre descriptivo",
                            on_change=ProcesosState.set_nuevo_nombre_proceso,
                            value=ProcesosState.nuevo_nombre_proceso,
                            width="100%"
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Crear Proceso",
                                on_click=ProcesosState.crear_proceso,
                                color_scheme="grass",
                                width="100%",
                                margin_top="4"
                            )
                        ),
                        spacing="3",
                    ),
                ),
            ),
            width="100%",
            margin_bottom="4"
        ),
        
        # Tabla de procesos
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("ID"),
                    rx.table.column_header_cell("Código del Proceso"),
                    rx.table.column_header_cell("Nombre"),
                    rx.table.column_header_cell("Fecha Creación"),
                    rx.table.column_header_cell("# Barridos"),
                    rx.table.column_header_cell("Acción"),
                )
            ),
            rx.table.body(
                rx.foreach(
                    ProcesosState.procesos,
                    lambda p: rx.table.row(
                        rx.table.cell(p.id.to_string()),
                        rx.table.cell(
                            rx.text(
                                p.codigo_proceso[:30] + "..." if len(p.codigo_proceso) > 30 else p.codigo_proceso,
                                font_family="monospace"
                            )
                        ),
                        rx.table.cell(p.nombre if p.nombre else "-"),
                        rx.table.cell(p.fecha_creacion.to_string()),
                        rx.table.cell("-"),  # TODO: Contar barridos
                        rx.table.cell(
                            rx.hstack(
                                rx.link(
                                    rx.button(
                                        rx.icon("eye"),
                                        "Ver Detalle",
                                        size="1",
                                        variant="soft",
                                        color_scheme="blue"
                                    ),
                                    href=f"/proceso/{p.id}"
                                ),
                                spacing="2"
                            )
                        ),
                    )
                )
            ),
            width="100%",
            variant="surface",
        ),
        
        spacing="5",
        width="100%",
        padding="4",
        on_mount=ProcesosState.load_procesos,
    )