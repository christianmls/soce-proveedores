import reflex as rx
from ..states.proveedores import ProveedoresState

def proveedores_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Base de Proveedores", size="7"),
            rx.spacer(),
            rx.dialog.root(
                rx.dialog.trigger(
                    rx.button("Agregar Proveedor", color_scheme="grass", icon="user-plus")
                ),
                rx.dialog.content(
                    rx.dialog.title("Nuevo Proveedor"),
                    rx.vstack(
                        rx.input(
                            placeholder="RUC (Obligatorio)", 
                            on_change=ProveedoresState.set_new_prov_ruc, 
                            value=ProveedoresState.new_prov_ruc
                        ),
                        rx.input(
                            placeholder="Nombre (Opcional)", 
                            on_change=ProveedoresState.set_new_prov_nombre, 
                            value=ProveedoresState.new_prov_nombre
                        ),
                        rx.input(
                            placeholder="Contacto (Opcional)", 
                            on_change=ProveedoresState.set_new_prov_contacto, 
                            value=ProveedoresState.new_prov_contacto
                        ),
                        # Selector de Categorías
                        rx.select.root(
                            rx.select.trigger(placeholder="Seleccionar Categoría..."),
                            rx.select.content(
                                rx.foreach(
                                    ProveedoresState.categorias, 
                                    lambda c: rx.select.item(c.nombre, value=c.id.to_string())
                                )
                            ),
                            on_change=ProveedoresState.set_new_prov_cat_id,
                            value=ProveedoresState.new_prov_cat_id,
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Guardar", 
                                on_click=ProveedoresState.add_proveedor, 
                                width="100%", 
                                color_scheme="grass"
                            )
                        ),
                        spacing="3",
                    ),
                ),
            ),
            width="100%",
        ),
        # Tabla de proveedores
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("RUC"),
                    rx.table.column_header_cell("Nombre"),
                    rx.table.column_header_cell("Contacto"),
                    rx.table.column_header_cell("Categoría"),
                )
            ),
            rx.table.body(
                rx.foreach(
                    ProveedoresState.proveedores, 
                    lambda p: rx.table.row(
                        rx.table.cell(p.ruc),
                        rx.table.cell(p.nombre),
                        rx.table.cell(p.contacto),
                        rx.table.cell(
                            rx.cond(
                                p.categoria_id,
                                "Categoría asignada",  # Puedes mejorar esto después
                                "Sin categoría"
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
        on_mount=ProveedoresState.load_data,  # <-- Carga datos al montar
    )