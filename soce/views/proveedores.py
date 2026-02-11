import reflex as rx
from ..states.proveedores import ProveedoresState

def proveedores_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Base de Proveedores", size="7"),
            rx.spacer(),
            rx.dialog.root(
                rx.dialog.trigger(rx.button("Agregar Proveedor", color_scheme="grass", icon="user-plus")),
                rx.dialog.content(
                    rx.dialog.title("Nuevo Proveedor"),
                    rx.vstack(
                        rx.input(placeholder="RUC (Obligatorio)", on_change=ProveedoresState.set_new_prov_ruc, value=ProveedoresState.new_prov_ruc),
                        rx.input(placeholder="Nombre (Opcional)", on_change=ProveedoresState.set_new_prov_nombre, value=ProveedoresState.new_prov_nombre),
                        
                        # Selector de Categorías (FK)
                        rx.select.root(
                            rx.select.trigger(placeholder="Seleccionar Categoría..."),
                            rx.select.content(
                                rx.foreach(
                                    # Accedemos a las categorías desde el State base
                                    ProveedoresState.categorias, 
                                    lambda c: rx.select.item(c.nombre, value=c.id.to_string())
                                )
                            ),
                            on_change=ProveedoresState.set_new_prov_cat_id,
                        ),
                        
                        rx.dialog.close(
                            rx.button("Guardar", on_click=ProveedoresState.add_proveedor, width="100%", color_scheme="grass")
                        ),
                        spacing="3",
                    ),
                ),
            ),
            width="100%",
        ),
        # ... (Tu tabla de proveedores actual aquí)
    )