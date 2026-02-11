import reflex as rx
from ..state import State

def procesos_view() -> rx.Component:
    return rx.vstack(
        # Encabezado y Acciones
        rx.hstack(
            rx.vstack(
                rx.heading("Barrido de Procesos", size="7"),
                rx.text("Configuración y monitoreo del scraper", color_scheme="gray"),
                align_items="start",
            ),
            rx.spacer(),
            rx.button(
                rx.cond(State.is_running, rx.spinner(size="1"), rx.icon("play")),
                "Iniciar Scraper",
                on_click=State.run_sweep,
                is_disabled=State.is_running,
                color_scheme="grass",
                size="3",
            ),
            width="100%",
            margin_bottom="1em",
        ),

        # Panel de Configuración y Logs
        rx.grid(
            # Columna Izquierda: Configuración
            rx.card(
                rx.vstack(
                    rx.text("URL del Proceso", weight="bold"),
                    rx.input(
                        placeholder="Pegue la URL del SOCE aquí...",
                        on_blur=State.set_url_base,
                        width="100%",
                    ),
                    rx.text("Parámetros adicionales", size="2", color_scheme="gray"),
                    rx.checkbox("Guardar capturas de pantalla", default_checked=False),
                    spacing="3",
                ),
                variant="surface",
            ),
            # Columna Derecha: Consola de Logs
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.text("Consola de Actividad", weight="bold"),
                        rx.badge(
                            rx.cond(State.is_running, "Ejecutando", "Ocioso"),
                            color_scheme=rx.cond(State.is_running, "amber", "gray"),
                        ),
                        justify="between",
                        width="100%",
                    ),
                    rx.scroll_area(
                        rx.code_block(
                            State.logs,
                            language="bash",
                            theme="nord",
                            custom_style={"fontSize": "0.8em", "height": "120px"},
                        ),
                        width="100%",
                    ),
                ),
                variant="surface",
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),

        rx.divider(),

        # Tabla de Resultados
        rx.vstack(
            rx.heading("Resultados del último barrido", size="4"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("RUC Proveedor"),
                        rx.table.column_header_cell("Objeto del Proceso"),
                        rx.table.column_header_cell("Valor Adjudicado"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        State.procesos,
                        lambda p: rx.table.row(
                            rx.table.cell(p.proveedor_ruc, font_family="monospace"),
                            rx.table.cell(p.objeto),
                            rx.table.cell(f"$ {p.valor}"),
                        )
                    )
                ),
                width="100%",
                variant="surface",
            ),
            width="100%",
            align_items="start",
        ),
        spacing="6",
        width="100%",
    )
