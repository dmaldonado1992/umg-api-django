from django.urls import path
from . import views

urlpatterns = [
    path('', views.usuarios_list_create, name='usuarios-list-create'),
    path('<int:pk>/inactivar/', views.inactivar_usuario, name='usuarios-inactivar'),
    path('<int:pk>/resetear-contrasena/', views.resetear_contrasena, name='usuarios-resetear-contrasena'),
]