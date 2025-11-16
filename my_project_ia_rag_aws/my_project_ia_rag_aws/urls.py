from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def redirect_to_docs(request):
    return redirect('/api/docs/')

urlpatterns = [
    path('', redirect_to_docs),  # Redireciona / para /api/docs/
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/', include('meu_app_rag.urls')),
]