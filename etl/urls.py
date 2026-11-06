from django.urls import path

from . import views

urlpatterns = [
    path("importar/", views.importar, name="importar"),
    path("exportar/", views.exportar, name="exportar"),
]