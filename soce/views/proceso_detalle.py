import reflex as rx
from ..states.procesos import ProcesosState

def oferta_row(oferta, ruc: str):
    """Fila de oferta individual"""
    return rx.cond(
        oferta.ruc_proveedor == ruc,
        rx.table.row(
            rx.table.cell(oferta.numero_item),
            rx.table.cell(
                rx.text(oferta.descripcion_producto, size="2"),
                max_width="600px"
            ),
            rx.table.cell(
                rx.text(f"{oferta.valor_total:,.5f}", align="right"),
                text_align="right"
            )
        ),
        rx.fragment()
    )

def anexo_badge(anexo, ruc: str):
    """Badge de anexo individual"""
    return rx.cond(
        anexo.ruc_proveedor == ruc,
        rx.badge(
            rx.icon("file-text", size=14),
            " ",
            anexo.nombre_archivo,
            color_scheme="blue",
            size="2"
        ),
        rx.fragment()
    )

def total_row_for_ruc(ruc: str):
    """Calcula y muestra el total para un RUC específico"""
    # Nota: Esto se calcula en el backend, no en el frontend
    # Por ahora solo mostramos la fila, el cálculo real viene de los datos
    return rx.table.row(
        rx.table.cell(""),
        rx.table.cell(
            rx.text("TOTAL:", weight="bold", align="right"),
            text_align="right"
        ),
        rx.table.cell(
            rx.text("USD.", weight="bold"),
            text_align="right"
        ),
        background_color=rx.color("gray", 3)
    )

def oferta_card(ruc: str):
    """Card de proveedor con sus ofertas"""
    return rx.card(
        rx.vstack(
            # Header
            rx.heading(f"Proveedor RUC: {ruc}", size="5", color_scheme="grass"),
            
            # Tabla de ofertas
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("No.", width="60px"),
                        rx.table.column_header_cell("Descripción"),
                        rx.table.column_header_cell("Total", width="150px", text_align="right")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.ofertas_actuales,
                        lambda o: oferta_row(o, ruc)
                    ),
                    # Fila de total (se mostrará para cada proveedor)
                    total_row_for_ruc(ruc)
                ),
                width="100%",
                variant="surface",
                size="2"
            ),
            
            # Anexos
            rx.cond(
                ProcesosState.anexos_actuales.length() > 0,
                rx.vstack(
                    rx.text("Documentos Anexos:", weight="bold", size="2", margin_top="3"),
                    rx.flex(
                        rx.foreach(
                            ProcesosState.anexos_actuales,
                            lambda a: anexo_badge(a, ruc)
                        ),
                        wrap="wrap",
                        spacing="2"
                    ),
                    width="100%",
                    align_items="start"
                ),
                rx.fragment()
            ),
            
            spacing="3",
            width="100%"
        ),
        width="100%",
        margin_bottom="4"
    )

def proceso_detalle_view():
    """Vista de detalle del proceso"""
    return rx.box(
        rx.vstack(
            # Header con botón volver
            rx.hstack(
                rx.button(
                    rx.icon("arrow-left", size=16),
                    "Volver",
                    on_click=lambda: ProcesosState.set_current_view("procesos"),
                    variant="ghost",
                    size="2"
                ),
                rx.spacer(),
                width="100%"
            ),
            
            # Panel de control
            rx.card(
                rx.hstack(
                    rx.button(
                        rx.cond(
                            ProcesosState.is_scraping,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Procesando..."),
                                spacing="2"
                            ),
                            rx.hstack(
                                rx.icon("play", size=16),
                                rx.text("Iniciar Barrido"),
                                spacing="2"
                            )
                        ),
                        on_click=ProcesosState.iniciar_scraping,
                        disabled=ProcesosState.is_scraping,
                        color_scheme="grass",
                        size="2"
                    ),
                    rx.text(
                        ProcesosState.scraping_progress,
                        size="2",
                        weight="medium"
                    ),
                    width="100%",
                    justify="between",
                    align_items="center"
                ),
                width="100%",
                margin_bottom="4"
            ),
            
            # Mensaje cuando no hay datos
            rx.cond(
                ProcesosState.rucs_unicos.length() == 0,
                rx.card(
                    rx.vstack(
                        rx.icon("inbox", size=48, color="gray"),
                        rx.text("No hay ofertas disponibles", size="4", weight="bold"),
                        rx.text("Inicia un barrido para ver resultados", size="2", color="gray"),
                        spacing="2",
                        align_items="center",
                        padding="6"
                    ),
                    width="100%"
                ),
                # Lista de ofertas
                rx.vstack(
                    rx.foreach(
                        ProcesosState.rucs_unicos,
                        oferta_card
                    ),
                    width="100%",
                    spacing="3"
                )
            ),
            
            spacing="4",
            width="100%"
        ),
        width="100%",
        height="100%",
        overflow_y="auto",
        padding="4"
    )