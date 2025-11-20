from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from django.conf import settings
from django.conf.urls.static import static

def redirect_to_docs(request):
    return redirect('/api/docs/')

urlpatterns = [
    path('', redirect_to_docs),  # Redireciona / para /api/docs/
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/', include('meu_app_rag.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)