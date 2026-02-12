import reflex as rx
from .views.categorias import categorias_view
from .views.proveedores import proveedores_view
from .views.procesos import procesos_view
from .views.proceso_detalle import proceso_detalle_view

def index() -> rx.Component:
    return rx.container(
        rx.hstack(
            # Sidebar
            rx.vstack(
                rx.heading("SOCE Pro", size="7", color_scheme="grass"),
                rx.divider(),
                rx.link(
                    rx.button(
                        rx.icon("search"),
                        "Procesos",
                        variant="ghost",
                        width="100%",
                        justify="start"
                    ),
                    href="/procesos"
                ),
                rx.link(
                    rx.button(
                        rx.icon("grid-2x2"),
                        "Categorías",
                        variant="ghost",
                        width="100%",
                        justify="start"
                    ),
                    href="/categorias"
                ),
                rx.link(
                    rx.button(
                        rx.icon("users"),
                        "Proveedores",
                        variant="ghost",
                        width="100%",
                        justify="start"
                    ),
                    href="/proveedores"
                ),
                spacing="2",
                width="200px",
                padding="4",
                background_color="gray.2",
                height="100vh",
            ),
            # Content
            rx.box(
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Procesos", value="procesos"),
                        rx.tabs.trigger("Categorías", value="categorias"),
                        rx.tabs.trigger("Proveedores", value="proveedores"),
                    ),
                    rx.tabs.content(procesos_view(), value="procesos"),
                    rx.tabs.content(categorias_view(), value="categorias"),
                    rx.tabs.content(proveedores_view(), value="proveedores"),
                    default_value="procesos",
                ),
                flex="1",
                padding="4",
            ),
            spacing="0",
            width="100%",
        ),
        max_width="100%",
        padding="0",
    )

app = rx.App()
app.add_page(index, route="/")
app.add_page(proceso_detalle_view, route="/proceso/[proceso_id]", on_load=lambda: rx.State.router.page.params)