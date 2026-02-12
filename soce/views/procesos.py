import reflex as rx
from ..states.procesos import ProcesosState

def oferta_detalle_card(oferta) -> rx.Component:
    """Componente para mostrar el detalle de cada oferta"""
    return rx.card(
        rx.vstack(
            # Header con datos del proveedor
            rx.heading("Datos del Proveedor", size="4", margin_bottom="3"),
            rx.grid(
                rx.vstack(
                    rx.hstack(rx.icon("user"), rx.text("RUC:", weight="bold"), rx.text(oferta.ruc_proveedor), spacing="2"),
                    rx.hstack(rx.icon("building"), rx.text("Razón Social:", weight="bold"), rx.text(oferta.razon_social), spacing="2"),
                    rx.hstack(rx.icon("mail"), rx.text("Correo electrónico:", weight="bold"), rx.text(oferta.correo_electronico), spacing="2"),
                    rx.hstack(rx.icon("phone"), rx.text("Teléfono:", weight="bold"), rx.text(oferta.telefono), spacing="2"),
                    spacing="2",
                    align_items="start",
                ),
                rx.vstack(
                    rx.hstack(rx.icon("flag"), rx.text("País:", weight="bold"), rx.text(oferta.pais), spacing="2"),
                    rx.hstack(rx.icon("map-pin"), rx.text("Provincia:", weight="bold"), rx.text(oferta.provincia), spacing="2"),
                    rx.hstack(rx.icon("map"), rx.text("Cantón:", weight="bold"), rx.text(oferta.canton), spacing="2"),
                    rx.hstack(rx.icon("home"), rx.text("Dirección:", weight="bold"), rx.text(oferta.direccion), spacing="2"),
                    spacing="2",
                    align_items="start",
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),
            
            # Tabla de productos
            rx.divider(margin_y="4"),
            rx.heading("Descripción del Producto", size="4", margin_bottom="3"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Descripción del Producto"),
                        rx.table.column_header_cell("Unidad"),
                        rx.table.column_header_cell("Cantidad"),
                        rx.table.column_header_cell("Valor Unitario Ofertado"),
                        rx.table.column_header_cell("Valor Total"),
                    )
                ),
                rx.table.body(
                    rx.table.row(
                        rx.table.cell(oferta.descripcion_producto),
                        rx.table.cell(oferta.unidad),
                        rx.table.cell(
                            rx.cond(
                                oferta.cantidad > 0,
                                rx.text(f"{oferta.cantidad:.2f}"),
                                rx.text("-")
                            )
                        ),
                        rx.table.cell(
                            rx.cond(
                                oferta.valor_unitario > 0,
                                rx.text(f"{oferta.valor_unitario:,.2f}"),
                                rx.text("-")
                            )
                        ),
                        rx.table.cell(
                            rx.cond(
                                oferta.valor_total > 0,
                                rx.text(f"{oferta.valor_total:,.5f}"),
                                rx.text("-")
                            )
                        ),
                    ),
                    rx.table.row(
                        rx.table.cell("", colspan=4, text_align="right"),
                        rx.table.cell(
                            rx.hstack(
                                rx.text("TOTAL:", weight="bold"),
                                rx.cond(
                                    oferta.valor_total > 0,
                                    rx.text(f"{oferta.valor_total:,.5f}", weight="bold"),
                                    rx.text("-", weight="bold")
                                ),
                                rx.text("USD.", weight="bold"),
                                spacing="2",
                                justify="end",
                            )
                        ),
                    ),
                ),
                variant="surface",
                width="100%",
            ),
            
            # Archivos (si existen)
            rx.cond(
                oferta.tiene_archivos,
                rx.vstack(
                    rx.divider(margin_y="4"),
                    rx.heading("Archivos", size="4"),
                    rx.text("Este proveedor tiene archivos adjuntos", color_scheme="blue"),
                    spacing="2",
                ),
                rx.box()
            ),
            
            spacing="4",
            width="100%",
        ),
        margin_bottom="4",
    )

def procesos_view() -> rx.Component:
    return rx.vstack(
        rx.heading("Barrido de Procesos", size="8"),
        rx.text("Configuración y monitoreo del scraper", color_scheme="gray"),
        
        # Panel de configuración y consola
        rx.hstack(
            # Panel de configuración
            rx.card(
                rx.vstack(
                    rx.heading("Nuevo Barrido", size="5"),
                    rx.text("ID del Proceso", size="2", weight="bold"),
                    rx.input(
                        placeholder="ID del proceso (ej: xrMof7bBhVxPzYlOopcMAsfszTSadIfpeUCMp99edjs)",
                        on_change=ProcesosState.set_proceso_url_id,
                        value=ProcesosState.proceso_url_id,
                        width="100%"
                    ),
                    rx.text("Categoría de Proveedores", size="2", weight="bold", margin_top="3"),
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
                    rx.button(
                        rx.cond(
                            ProcesosState.is_scraping,
                            "⏳ Procesando...",
                            "▶️ Iniciar Scraping"
                        ),
                        on_click=ProcesosState.iniciar_scraping,
                        color_scheme="grass",
                        size="3",
                        disabled=ProcesosState.is_scraping,
                        width="100%",
                        margin_top="4"
                    ),
                    spacing="3",
                    width="100%"
                ),
                width="50%"
            ),
            
            # Consola de actividad
            rx.card(
                rx.vstack(
                    rx.heading("Consola de Actividad", size="5"),
                    rx.box(
                        rx.text(
                            ProcesosState.scraping_progress,
                            white_space="pre-wrap"
                        ),
                        padding="4",
                        background_color="gray.2",
                        border_radius="md",
                        min_height="200px",
                        max_height="400px",
                        overflow_y="auto",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),
                width="50%"
            ),
            spacing="4",
            width="100%"
        ),
        
        # Historial de barridos
        rx.divider(margin_y="6"),
        rx.heading("Historial de Barridos", size="6", margin_bottom="4"),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("ID"),
                    rx.table.column_header_cell("Fecha Inicio"),
                    rx.table.column_header_cell("Fecha Fin"),
                    rx.table.column_header_cell("Total"),
                    rx.table.column_header_cell("Exitosos"),
                    rx.table.column_header_cell("Sin Datos"),
                    rx.table.column_header_cell("Errores"),
                    rx.table.column_header_cell("Estado"),
                    rx.table.column_header_cell("Acción"),
                )
            ),
            rx.table.body(
                rx.foreach(
                    ProcesosState.barridos,
                    lambda b: rx.table.row(
                        rx.table.cell(b.id.to_string()),
                        rx.table.cell(
                            rx.cond(
                                b.fecha_inicio,
                                rx.text(b.fecha_inicio.strftime("%Y-%m-%d %H:%M") if b.fecha_inicio else "-"),
                                rx.text("-")
                            )
                        ),
                        rx.table.cell(
                            rx.cond(
                                b.fecha_fin,
                                rx.text(b.fecha_fin.strftime("%Y-%m-%d %H:%M") if b.fecha_fin else "-"),
                                rx.text("-")
                            )
                        ),
                        rx.table.cell(b.total_proveedores.to_string()),
                        rx.table.cell(b.exitosos.to_string()),
                        rx.table.cell(b.sin_datos.to_string()),
                        rx.table.cell(b.errores.to_string()),
                        rx.table.cell(
                            rx.badge(
                                b.estado,
                                color_scheme=rx.cond(
                                    b.estado == "completado",
                                    "green",
                                    rx.cond(
                                        b.estado == "error",
                                        "red",
                                        "blue"
                                    )
                                )
                            )
                        ),
                        rx.table.cell(
                            rx.button(
                                "Ver Ofertas",
                                on_click=lambda: ProcesosState.set_barrido_seleccionado(b.id.to_string()),
                                size="1",
                                variant="soft"
                            )
                        ),
                    )
                )
            ),
            width="100%",
            variant="surface",
            margin_bottom="6"
        ),
        
        # Ofertas del barrido seleccionado
        rx.cond(
            ProcesosState.barrido_seleccionado_id,
            rx.vstack(
                rx.divider(margin_y="6"),
                rx.heading(
                    f"Ofertas del Barrido #{ProcesosState.barrido_seleccionado_id}", 
                    size="6", 
                    margin_bottom="4"
                ),
                rx.foreach(
                    ProcesosState.ofertas_actuales,
                    lambda o: rx.cond(
                        o.estado == "procesado",
                        oferta_detalle_card(o),
                        rx.box()  # No mostrar los que no tienen datos
                    )
                ),
                width="100%"
            ),
            rx.box()
        ),
        
        spacing="5",
        width="100%",
        padding="4",
        on_mount=lambda: [ProcesosState.load_categorias(), ProcesosState.load_barridos()],
    )