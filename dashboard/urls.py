from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", views.painel, name="dashboard"),
    path(
        "privacidade/",
        TemplateView.as_view(template_name="dashboard/privacidade.html"),
        name="privacidade",
    ),
]