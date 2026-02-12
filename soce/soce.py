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
            rx.text(text, font_weight="medium"),
            spacing="3", align_items="center", width="100%",
        ),
        # Usamos ProcesosState.current_view para saber cuál está activa
        variant=rx.cond(ProcesosState.current_view == page_value, "solid", "ghost"),
        color_scheme="grass", 
        width="100%", 
        justify="start", 
        padding="3",
        # CORRECCIÓN AQUÍ: El setter automático de 'current_view' es 'set_current_view'
        on_click=lambda: ProcesosState.set_current_view(page_value), 
        cursor="pointer",
    )

def index() -> rx.Component:
    return rx.hstack(
        # --- SIDEBAR ---
        rx.vstack(
            rx.heading("SOCE Pro", size="6", color_scheme="grass", margin_bottom="4"),
            rx.divider(margin_bottom="4"),
            rx.vstack(
                sidebar_item("Procesos", "search", "procesos"),
                sidebar_item("Categorías", "grid-2x2", "categorias"),
                sidebar_item("Proveedores", "users", "proveedores"),
                spacing="2", width="100%"
            ),
            width="250px", height="100vh", padding="6",
            background_color=rx.color("gray", 2),
            border_right=f"1px solid {rx.color('gray', 4)}",
            position="sticky", top="0",
        ),

        # --- CONTENIDO PRINCIPAL ---
        rx.box(
            rx.match(
                ProcesosState.current_view,
                ("procesos", procesos_view()),
                ("categorias", categorias_view()),
                ("proveedores", proveedores_view()),
                ("detalle_proceso", proceso_detalle_view()), # Vista interna de detalle
                procesos_view() # Default
            ),
            flex="1", padding="8",
            background_color=rx.color("gray", 1),
            min_height="100vh", width="100%",
        ),
        spacing="0", width="100%",
    )

app = rx.App()
app.add_page(index, route="/")