import reflex as rx
from ..states.procesos import ProcesosState

def oferta_row(oferta, ruc: str):
    """Fila de oferta individual"""
    return rx.cond(
        oferta.ruc_proveedor == ruc,
        rx.table.row(
            rx.table.cell(oferta.numero_item),
            rx.table.cell(oferta.descripcion_producto),
            rx.table.cell(f"{oferta.valor_total:,.2f}")
        ),
        rx.fragment()
    )

def anexo_badge(anexo, ruc: str):
    """Badge de anexo individual"""
    return rx.cond(
        anexo.ruc_proveedor == ruc,
        rx.link(
            rx.badge(
                rx.icon("file-down", size=14),
                anexo.nombre_archivo,
                color_scheme="blue"
            ),
            href=anexo.url_archivo,
            is_external=True
        ),
        rx.fragment()
    )

def oferta_card(ruc: str):
    """Card de proveedor con sus ofertas"""
    return rx.card(
        rx.vstack(
            rx.heading(f"Proveedor RUC: {ruc}", size="4", color_scheme="grass"),
            
            # Tabla de ofertas
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("No."),
                        rx.table.column_header_cell("Descripción"),
                        rx.table.column_header_cell("Total")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        ProcesosState.ofertas_actuales,
                        lambda o: oferta_row(o, ruc)
                    )
                ),
                width="100%",
                variant="surface"
            ),
            
            # Sección de anexos
            rx.vstack(
                rx.text("Documentos Anexos:", weight="bold", size="2"),
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
            
            width="100%",
            spacing="3"
        ),
        width="100%",
        margin_bottom="4"
    )

def proceso_detalle_view():
    """Vista de detalle del proceso con ofertas agrupadas por proveedor"""
    return rx.vstack(
        # Botón volver
        rx.button(
            rx.icon("arrow-left"),
            "Volver",
            on_click=lambda: ProcesosState.set_current_view("procesos"),
            variant="ghost",
            margin_bottom="4"
        ),
        
        # Panel de control del barrido
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
                            rx.icon("play"),
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
                    weight="bold",
                    size="2"
                ),
                width="100%",
                justify="between",
                align_items="center"
            ),
            width="100%",
            margin_bottom="6"
        ),
        
        # Lista de ofertas agrupadas por RUC
        rx.vstack(
            rx.foreach(
                ProcesosState.rucs_unicos,
                oferta_card
            ),
            width="100%",
            align_items="stretch"
        ),
        
        width="100%",
        padding="4",
        align_items="stretch"
    )