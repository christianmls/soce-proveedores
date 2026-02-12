import reflex as rx
from .views.categorias import categorias_view
from .views.proveedores import proveedores_view
from .views.procesos import procesos_view
from .views.proceso_detalle import proceso_detalle_view

# 1. Creamos un Estado para controlar la navegación del menú lateral
class NavState(rx.State):
    current_page: str = "procesos"

    def set_page(self, page_name: str):
        self.current_page = page_name

def sidebar_item(text: str, icon: str, page_value: str) -> rx.Component:
    """Componente reutilizable para los botones del menú"""
    return rx.button(
        rx.hstack(
            rx.icon(icon, size=20),
            rx.text(text, font_weight="medium"),
            spacing="3",
            align_items="center",
            width="100%",
        ),
        # Si esta es la página actual, usamos variant="solid" (resaltado), si no "ghost"
        variant=rx.cond(
            NavState.current_page == page_value,
            "solid",
            "ghost"
        ),
        color_scheme="grass",  # Mantenemos tu color
        width="100%",
        justify="start",
        padding="3",
        on_click=lambda: NavState.set_page(page_value),
        cursor="pointer",
    )

def index() -> rx.Component:
    return rx.hstack(
        # --- SIDEMENU (Izquierda) ---
        rx.vstack(
            rx.heading("SOCE Pro", size="6", color_scheme="grass", margin_bottom="4"),
            rx.divider(margin_bottom="4"),
            
            # Botones de navegación conectados al estado
            rx.vstack(
                sidebar_item("Procesos", "search", "procesos"),
                sidebar_item("Categorías", "grid-2x2", "categorias"),
                sidebar_item("Proveedores", "users", "proveedores"),
                spacing="2",
                width="100%"
            ),
            
            width="250px",
            height="100vh",
            padding="6",
            background_color=rx.color("gray", 2),
            border_right=f"1px solid {rx.color('gray', 4)}",
            position="sticky",
            top="0",
        ),

        # --- CONTENIDO PRINCIPAL (Derecha) ---
        rx.box(
            # Usamos rx.match para cambiar la vista según el estado actual
            rx.match(
                NavState.current_page,
                ("procesos", procesos_view()),
                ("categorias", categorias_view()),
                ("proveedores", proveedores_view()),
                procesos_view() # Default por si acaso
            ),
            flex="1",
            padding="8",
            background_color=rx.color("gray", 1),
            min_height="100vh",
            width="100%",
        ),
        spacing="0",
        width="100%",
    )

app = rx.App()
app.add_page(index, route="/")
app.add_page(proceso_detalle_view, route="/proceso/[pid]")