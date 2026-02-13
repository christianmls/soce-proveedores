import reflex as rx
from ..states.procesos import ProcesosState

def oferta_row(oferta, ruc: str):
    """Fila de oferta individual"""
    return rx.cond(
        oferta.ruc_proveedor == ruc,
        rx.table.row(
            rx.table.cell(oferta.numero_item, width="60px"),
            rx.table.cell(
                rx.text(oferta.descripcion_producto, size="2")
            ),
            rx.table.cell(
                rx.text(f"{oferta.valor_total:,.5f}", align="right"),
                text_align="right",
                width="150px"
            )
        ),
        rx.fragment()
    )

def anexo_badge(anexo, ruc: str):
    """Badge de anexo como link externo"""
    return rx.cond(
        anexo.ruc_proveedor == ruc,
        rx.link(
            rx.button(
                rx.icon("file-down", size=14),
                " ",
                anexo.nombre_archivo,
                variant="soft",
                color_scheme="blue",
                size="2"
            ),
            href=anexo.url_archivo,
            is_external=True
        ),
        rx.fragment()
    )

def total_row_for_ruc(ruc: str):
    """Muestra el total para un RUC específico"""
    total = ProcesosState.totales_por_ruc.get(ruc, 0.0)
    
    return rx.table.row(
        rx.table.cell(""),
        rx.table.cell(
            rx.text("TOTAL:", weight="bold", align="right"),
            text_align="right"
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(f"{total:,.5f}", weight="bold", size="3"),
                rx.text("USD.", weight="bold"),
                spacing="2",
                justify="end"
            ),
            text_align="right"
        ),
        background_color=rx.color("gray", 3)
    )

def datos_proveedor_row(oferta, ruc: str):
    """Muestra datos del proveedor - solo la primera vez"""
    return rx.cond(
        oferta.ruc_proveedor == ruc,
        rx.card(
            rx.vstack(
                rx.heading("Datos del Proveedor", size="4", margin_bottom="3"),
                rx.grid(
                    rx.hstack(
                        rx.icon("user", size=16),
                        rx.text("RUC:", weight="bold", size="2"),
                        rx.text(oferta.ruc_proveedor, size="2"),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.icon("building", size=16),
                        rx.text("Razón Social:", weight="bold", size="2"),
                        rx.text(oferta.razon_social or "N/A", size="2"),
                        spacing="2"
                    ),
                    columns="1",
                    spacing="2",
                    width="100%"
                ),
                spacing="3",
                width="100%"
            ),
            width="100%",
            margin_bottom="4"
        ),
        rx.fragment()
    )

def oferta_card(ruc: str):
    """Card de proveedor con sus ofertas"""
    return rx.vstack(
        # Título del proveedor
        rx.heading(f"Proveedor RUC: {ruc}", size="5", color_scheme="grass"),
        
        # Datos del proveedor - usar foreach para obtener la primera oferta
        rx.foreach(
            ProcesosState.ofertas_actuales,
            lambda o: datos_proveedor_row(o, ruc),
            # Solo se renderizará una vez porque datos_proveedor_row retorna fragment después
        ),
        
        # Tabla de ofertas
        rx.card(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("No."),
                        rx.table.column_header_cell("Descripción"),
                        rx.table.column_header_cell("Total", text_align="right")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.ofertas_actuales,
                        lambda o: oferta_row(o, ruc)
                    ),
                    total_row_for_ruc(ruc)
                ),
                width="100%",
                variant="surface",
                size="2"
            ),
            width="100%"
        ),
        
        # Anexos
        rx.cond(
            ProcesosState.anexos_actuales.length() > 0,
            rx.card(
                rx.vstack(
                    rx.text("Documentos Anexos:", weight="bold", size="3"),
                    rx.flex(
                        rx.foreach(
                            ProcesosState.anexos_actuales,
                            lambda a: anexo_badge(a, ruc)
                        ),
                        wrap="wrap",
                        spacing="2"
                    ),
                    width="100%",
                    align_items="start",
                    spacing="3"
                ),
                width="100%"
            ),
            rx.fragment()
        ),
        
        spacing="4",
        width="100%",
        margin_bottom="6"
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
                width="100%",
                margin_bottom="4"
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
                        size="3"
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
                width="100%"
            ),
            
            # Mensaje cuando no hay datos
            rx.cond(
                ProcesosState.rucs_unicos.length() == 0,
                rx.card(
                    rx.vstack(
                        rx.icon("inbox", size=48, color="gray"),
                        rx.text("No hay ofertas disponibles", size="4", weight="bold"),
                        rx.text("Inicia un barrido para ver resultados", size="2", color="gray"),
                        spacing="3",
                        align_items="center",
                        padding="8"
                    ),
                    width="100%",
                    margin_top="6"
                ),
                # Lista de ofertas
                rx.vstack(
                    rx.foreach(
                        ProcesosState.rucs_unicos,
                        oferta_card
                    ),
                    width="100%",
                    spacing="6",
                    margin_top="6"
                )
            ),
            
            spacing="6",
            width="100%"
        ),
        padding="32px",
        width="100%"
    )