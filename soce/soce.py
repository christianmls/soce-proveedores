import reflex as rx
from .views.categorias import categorias_view
from .views.proveedores import proveedores_view
from .views.procesos import procesos_view
from .views.proceso_detalle import proceso_detalle_view
from .states.procesos import ProcesosState 

def sidebar_item(text: str, icon: str, page_value: str) -> rx.Component:
    """Item del sidebar con highlight cuando está activo"""
    return rx.box(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text, size="2", weight="medium"),
            spacing="3",
            align_items="center",
            width="100%"
        ),
        on_click=lambda: ProcesosState.set_current_view(page_value),
        padding="10px 16px",
        border_radius="8px",
        cursor="pointer",
        background_color=rx.cond(
            ProcesosState.current_view == page_value,
            rx.color("grass", 3),
            "transparent"
        ),
        color=rx.cond(
            ProcesosState.current_view == page_value,
            rx.color("grass", 11),
            rx.color("gray", 11)
        ),
        _hover={
            "background_color": rx.cond(
                ProcesosState.current_view == page_value,
                rx.color("grass", 4),
                rx.color("gray", 3)
            )
        },
        width="100%"
    )

def index() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Sidebar
            rx.vstack(
                # Logo/Header
                rx.vstack(
                    rx.heading("SOCE Pro", size="6", color_scheme="grass"),
                    rx.text("Sistema de Ofertas", size="1", color="gray"),
                    spacing="1",
                    align_items="start",
                    width="100%",
                    padding_bottom="4"
                ),
                
                rx.divider(),
                
                # Menu items
                rx.vstack(
                    sidebar_item("Procesos", "search", "procesos"),
                    sidebar_item("Categorías", "grid-2x2", "categorias"),
                    sidebar_item("Proveedores", "users", "proveedores"),
                    spacing="1",
                    width="100%",
                    padding_top="4"
                ),
                
                spacing="4",
                width="240px",
                height="100vh",
                padding="20px 16px",
                background_color=rx.color("gray", 2),
                border_right=f"1px solid {rx.color('gray', 4)}",
                align_items="start"
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
            height="100vh",
            align_items="stretch"
        ),
        width="100vw",
        height="100vh",
        overflow="hidden"
    )

app = rx.App()
app.add_page(index, route="/")