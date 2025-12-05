# conhecimento/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, ImportViewSet, KnowledgeBaseViewSet, DocumentoViewSet

router = DefaultRouter()
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'import', ImportViewSet, basename='import')
router.register(r'bases', KnowledgeBaseViewSet, basename='bases')
router.register(r'documentos', DocumentoViewSet, basename='documentos')

urlpatterns = [
    path('api/', include(router.urls)),
]