import reflex as rx
from ..state import State

def menu_item(text: str, icon: str, page: str) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.icon(icon, size=20),
            rx.text(text),
            spacing="3",
        ),
        on_click=lambda: State.set_page(page),
        variant="ghost",
        width="100%",
        justify="start",
        color_scheme=rx.cond(State.current_page == page, "grass", "gray"),
    )

def sidebar() -> rx.Component:
    return rx.vstack(
        rx.heading("SOCE Pro", size="6", margin_bottom="1em", color_scheme="grass"),
        menu_item("Procesos", "search", "procesos"),
        menu_item("Categorías", "layout-grid", "categorias"),
        menu_item("Proveedores", "users", "proveedores"),
        width="250px",
        height="100vh",
        padding="2em",
        background_color=rx.color("gray", 2),
        border_right=f"1px solid {rx.color('gray', 4)}",
    )
