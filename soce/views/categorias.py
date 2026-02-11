import reflex as rx
from ..states.categorias import CategoriaState as State

def categorias_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Gestión de Categorías", size="7"),
            rx.spacer(),
            rx.dialog.root(
                rx.dialog.trigger(rx.button("Nueva Categoría", color_scheme="grass", icon="plus")),
                rx.dialog.content(
                    rx.dialog.title("Añadir Categoría"),
                    rx.vstack(
                        rx.input(placeholder="Nombre", on_change=State.set_new_cat_nombre, value=State.new_cat_nombre),
                        rx.dialog.close(
                            rx.button("Guardar", on_click=State.add_categoria, width="100%")
                        ),
                        spacing="3",
                    ),
                ),
            ),
            width="100%",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Nombre"),
                    rx.table.column_header_cell("Descripción"),
                )
            ),
            rx.table.body(
                rx.foreach(State.categorias, lambda c: rx.table.row(
                    rx.table.cell(c.nombre),
                    rx.table.cell(c.descripcion)
                ))
            ),
            width="100%",
            variant="surface",
        ),
        spacing="5",
        width="100%",
    )
