import reflex as rx
from .views.procesos import procesos_view
from .views.proceso_detalle import proceso_detalle_view
from .states.procesos import ProcesosState 

def index() -> rx.Component:
    return rx.hstack(
        # Sidebar
        rx.vstack(
            rx.heading("SOCE Pro", size="6", color_scheme="grass"),
            rx.button("Procesos", on_click=lambda: ProcesosState.set_current_view("procesos"), width="100%"),
            width="250px", height="100vh", padding="6", background_color=rx.color("gray", 2)
        ),
        # Contenido Principal
        rx.box(
            rx.match(
                ProcesosState.current_view,
                ("procesos", procesos_view()),
                ("detalle_proceso", proceso_detalle_view()),
                procesos_view()
            ),
            flex="1", width="100%", min_height="100vh", padding="8" # Expande al 100%
        ),
        spacing="0", width="100%", height="100vh", align_items="stretch"
    )

app = rx.App()
app.add_page(index, route="/")