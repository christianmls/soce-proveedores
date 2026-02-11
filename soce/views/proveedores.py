import reflex as rx
from ..states.proveedores import ProveedorState as State

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
                        rx.input(placeholder="RUC", on_change=State.set_new_prov_ruc, value=State.new_prov_ruc),
                        rx.input(placeholder="Nombre", on_change=State.set_new_prov_nombre, value=State.new_prov_nombre),
                        rx.dialog.close(
                            rx.button("Guardar", on_click=State.add_proveedor, width="100%")
                        ),
                        spacing="3",
                    ),
                ),
            ),
            width="100%",
        ),
        rx.table.root(
            rx.table.header(rx.table.row(rx.table.column_header_cell("RUC"), rx.table.column_header_cell("Nombre"))),
            rx.table.body(
                rx.foreach(State.proveedores, lambda p: rx.table.row(rx.table.cell(p.ruc), rx.table.cell(p.nombre)))
            ),
            width="100%",
            variant="surface",
        ),
        width="100%",
        spacing="5",
    )
