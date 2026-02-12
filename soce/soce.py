import reflex as rx
from .views.categorias import categorias_view
from .views.proveedores import proveedores_view
from .views.procesos import procesos_view
from .views.proceso_detalle import proceso_detalle_view
from .states.procesos import ProcesosState 

def sidebar_item(text: str, icon: str, page_value: str) -> rx.Component:
    return rx.button(
        rx.hstack(rx.icon(icon, size=20), rx.text(text), spacing="3", align_items="center"),
        variant=rx.cond(ProcesosState.current_view == page_value, "solid", "ghost"),
        color_scheme="grass", width="100%", justify="start",
        on_click=lambda: ProcesosState.set_current_view(page_value), 
    )

def index() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.heading("SOCE Pro", size="6", color_scheme="grass"),
            rx.divider(),
            sidebar_item("Procesos", "search", "procesos"),
            sidebar_item("Categorías", "grid-2x2", "categorias"),
            sidebar_item("Proveedores", "users", "proveedores"),
            width="250px", height="100vh", padding="6", background_color=rx.color("gray", 2), border_right=f"1px solid {rx.color('gray', 4)}",
        ),
        rx.box(
            rx.match(
                ProcesosState.current_view,
                ("procesos", procesos_view()),
                ("categorias", categorias_view()),
                ("proveedores", proveedores_view()),
                ("detalle_proceso", proceso_detalle_view()),
                procesos_view()
            ),
            flex="1", padding="8", background_color=rx.color("gray", 1), min_height="100vh",
        ),
        spacing="0", width="100%",
    )

app = rx.App()
app.add_page(index, route="/")