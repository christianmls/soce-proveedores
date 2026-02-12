import reflex as rx
from .views.categorias import categorias_view
from .views.proveedores import proveedores_view
from .views.procesos import procesos_view
from .views.proceso_detalle import proceso_detalle_view
from .states.procesos import ProcesosState 

def sidebar_item(text: str, icon: str, page_value: str) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.icon(icon, size=20), 
            rx.text(text, size="2"), 
            spacing="2", 
            align_items="center"
        ),
        variant=rx.cond(
            ProcesosState.current_view == page_value, 
            "solid", 
            "ghost"
        ),
        color_scheme="grass", 
        width="100%", 
        justify="start",
        size="2",
        on_click=lambda: ProcesosState.set_current_view(page_value)
    )

def index() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Sidebar
            rx.vstack(
                rx.heading("SOCE Pro", size="6", color_scheme="grass", margin_bottom="4"),
                rx.divider(),
                sidebar_item("Procesos", "search", "procesos"),
                sidebar_item("Categorías", "grid-2x2", "categorias"),
                sidebar_item("Proveedores", "users", "proveedores"),
                width="220px", 
                height="100vh", 
                padding="4", 
                background_color=rx.color("gray", 2),
                spacing="2"
            ),
            
            # Contenido principal
            rx.box(
                rx.match(
                    ProcesosState.current_view,
                    ("procesos", procesos_view()),
                    ("categorias", categorias_view()),
                    ("proveedores", proveedores_view()),
                    ("detalle_proceso", proceso_detalle_view()),
                    procesos_view()
                ),
                flex="1",
                height="100vh",
                overflow_y="auto",
                background_color=rx.color("gray", 1)
            ),
            
            spacing="0",
            width="100%",
            height="100vh"
        ),
        width="100vw",
        height="100vh",
        overflow="hidden"
    )

app = rx.App()
app.add_page(index, route="/")