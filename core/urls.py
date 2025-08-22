
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("proposito/", views.proposito, name="proposito"),
    path("renca/nueva/", views.renca_nueva, name="renca_nueva"),
    path("renca/<int:pk>/ver/", views.renca_ver, name="renca_ver"),
    path("renca/<int:pk>/tablas/", views.renca_tablas, name="renca_tablas"),
    path("renca/<int:pk>/analizar/", views.renca_analizar, name="renca_analizar"),
    path("renca/<int:pk>/pdf/", views.renca_pdf, name="renca_pdf"),

    



]
