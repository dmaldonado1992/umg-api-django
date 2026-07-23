from django.contrib import admin
from django.urls import path, include
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/labs/', include('labs.urls')),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/reservas/', include('reservas.urls')),
    path('api/condiciones/', include('condiciones.urls')),
    path('api/auth/login/', usuarios_views.login, name='auth-login'),
    path('api/auth/cambiar-contrasena/', usuarios_views.cambiar_contrasena, name='auth-cambiar-contrasena'),
    path('api/logs/', include('logs.urls')),
]