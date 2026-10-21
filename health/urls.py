from django.urls import path
from . import views

urlpatterns = [
    path("", views.liveness, name="liveness"),
]