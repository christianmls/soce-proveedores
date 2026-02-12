import reflex as rx
from ..states.procesos import ProcesosState

def procesos_view() -> rx.Component:
    return rx.vstack(
        rx.heading("Procesos de Contratación", size="8"),
        rx.text("Gestión de procesos y barridos", color_scheme="gray"),
        
        # --- MODAL DE CREACIÓN ---
        rx.dialog.root(
            rx.dialog.trigger(
                rx.button(rx.icon("plus"), "Nuevo Proceso", color_scheme="grass")
            ),
            rx.dialog.content(
                rx.dialog.title("Crear Nuevo Proceso"),
                rx.vstack(
                    rx.text("Código del Proceso", size="2", weight="bold"),
                    rx.input(
                        placeholder="Ej: xrMof...", 
                        on_change=ProcesosState.set_nuevo_codigo_proceso,
                        value=ProcesosState.nuevo_codigo_proceso,
                        width="100%"
                    ),
                    
                    rx.text("Nombre (Opcional)", size="2", weight="bold"),
                    rx.input(
                        placeholder="Descripción corta", 
                        on_change=ProcesosState.set_nuevo_nombre_proceso,
                        value=ProcesosState.nuevo_nombre_proceso,
                        width="100%"
                    ),
                    
                    # --- AQUÍ ESTÁ EL SELECTOR DE CATEGORÍA ---
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
                        width="100%",
                    ),
                    
                    rx.dialog.close(
                        rx.button(
                            "Guardar", 
                            on_click=ProcesosState.crear_proceso, 
                            color_scheme="grass", 
                            width="100%",
                            margin_top="2"
                        )
                    ),
                    spacing="3"
                )
            )
        ),
        
        # --- TABLA DE PROCESOS ---
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
                            rx.button(
                                rx.icon("eye"), 
                                size="1", 
                                variant="soft",
                                on_click=lambda: ProcesosState.ir_a_detalle(p["id"]),
                                cursor="pointer"
                            )
                        ),
                    )
                )
            ),
            width="100%", variant="surface",
        ),
        
        # Cargamos procesos y categorías al entrar
        on_mount=[ProcesosState.load_procesos, ProcesosState.load_categorias],
        spacing="5", padding="4", width="100%"
    )