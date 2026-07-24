from django.contrib import admin
from django.urls import path, include
from usuarios import views as usuarios_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/labs/', include('labs.urls')),
    path('api/usuarios/', include('usuarios.urls')),
    path('api/reservas/', include('reservas.urls')),
    path('api/condiciones/', include('condiciones.urls')),
    path('api/auth/login/', usuarios_views.login, name='auth-login'),
    path('api/auth/cambiar-contrasena/', usuarios_views.cambiar_contrasena, name='auth-cambiar-contrasena'),
    path('api/logs/', include('logs.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]