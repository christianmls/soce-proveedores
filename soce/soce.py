import reflex as rx
from .state import State
from .components.sidebar import sidebar
from .views.procesos import procesos_view
from .views.categorias import categorias_view
from .views.proveedores import proveedores_view

def index() -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(
            rx.match(
                State.current_page,
                ("procesos", procesos_view()),
                ("categorias", categorias_view()),
                ("proveedores", proveedores_view()),
                procesos_view(),
            ),
            padding="2em",
            width="100%",
        ),
        width="100%",
        spacing="0",
    )

app = rx.App(theme=rx.theme(appearance="dark", accent_color="grass", radius="large"))
app.add_page(index, on_load=State.on_load)
