import reflex as rx
from ..states.procesos import ProcesosState

def procesos_view():
    """Vista de listado de procesos mejorada"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Procesos de Contratación", size="7"),
                rx.spacer(),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.button(
                            rx.icon("plus", size=18),
                            "Nuevo Proceso",
                            color_scheme="grass",
                            size="3"
                        )
                    ),
                    rx.dialog.content(
                        rx.dialog.title("Crear Nuevo Proceso"),
                        rx.dialog.description(
                            "Ingresa los datos del proceso de contratación"
                        ),
                        rx.vstack(
                            rx.vstack(
                                rx.text("Código del Proceso", size="2", weight="bold"),
                                rx.input(
                                    placeholder="ej: PEK4fvqKamCKkU3DU_Ota3z...",
                                    on_change=ProcesosState.set_nuevo_codigo_proceso,
                                    value=ProcesosState.nuevo_codigo_proceso,
                                    width="100%"
                                ),
                                width="100%",
                                align_items="start",
                                spacing="2"
                            ),
                            rx.vstack(
                                rx.text("Nombre (opcional)", size="2", weight="bold"),
                                rx.input(
                                    placeholder="Nombre descriptivo del proceso",
                                    on_change=ProcesosState.set_nuevo_nombre_proceso,
                                    value=ProcesosState.nuevo_nombre_proceso,
                                    width="100%"
                                ),
                                width="100%",
                                align_items="start",
                                spacing="2"
                            ),
                            rx.vstack(
                                rx.text("Categoría", size="2", weight="bold"),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Seleccionar Categoría..."),
                                    rx.select.content(
                                        rx.foreach(
                                            ProcesosState.categorias,
                                            lambda c: rx.select.item(c.nombre, value=c.id.to_string())
                                        )
                                    ),
                                    on_change=ProcesosState.set_categoria_id,
                                    value=ProcesosState.categoria_id,
                                    width="100%"
                                ),
                                width="100%",
                                align_items="start",
                                spacing="2"
                            ),
                            rx.hstack(
                                rx.dialog.close(
                                    rx.button(
                                        "Cancelar",
                                        variant="soft",
                                        color_scheme="gray"
                                    )
                                ),
                                rx.dialog.close(
                                    rx.button(
                                        "Guardar",
                                        on_click=ProcesosState.crear_proceso,
                                        color_scheme="grass"
                                    )
                                ),
                                spacing="3",
                                justify="end",
                                width="100%"
                            ),
                            spacing="4",
                            width="100%"
                        ),
                        max_width="500px"
                    )
                ),
                width="100%",
                align_items="center",
                margin_bottom="6"
            ),
            
            # Tabla de procesos
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Código"),
                        rx.table.column_header_cell("Nombre"),
                        rx.table.column_header_cell("Fecha Creación"),
                        rx.table.column_header_cell("Acciones", width="150px")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.lista_procesos_formateada,
                        lambda p: rx.table.row(
                            rx.table.cell(
                                rx.text(
                                    p["codigo"][:40] + "..." if len(p["codigo"]) > 40 else p["codigo"],
                                    font_family="monospace",
                                    size="2"
                                )
                            ),
                            rx.table.cell(
                                rx.text(
                                    ProcesosState.procesos[0].nombre if ProcesosState.procesos else "-",
                                    size="2"
                                )
                            ),
                            rx.table.cell(
                                rx.text(p["fecha"], size="2", color="gray")
                            ),
                            rx.table.cell(
                                rx.hstack(
                                    rx.button(
                                        rx.icon("eye", size=16),
                                        on_click=lambda: ProcesosState.ir_a_detalle(p["id"]),
                                        size="1",
                                        variant="soft",
                                        color_scheme="blue"
                                    ),
                                    rx.button(
                                        rx.icon("trash-2", size=16),
                                        on_click=lambda: ProcesosState.eliminar_proceso(p["id"]),
                                        size="1",
                                        variant="soft",
                                        color_scheme="red"
                                    ),
                                    spacing="2"
                                )
                            )
                        )
                    )
                ),
                width="100%",
                variant="surface"
            ),
            
            spacing="6",
            width="100%"
        ),
        padding="32px",
        width="100%"
    )