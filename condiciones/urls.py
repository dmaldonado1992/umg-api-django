from django.urls import path
from . import views

urlpatterns = [
    path('', views.condiciones_list_create, name='condiciones-list-create'),
    path('<int:pk>/', views.condiciones_update, name='condiciones-update'),
]