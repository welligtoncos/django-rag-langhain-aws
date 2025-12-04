# conhecimento/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, ImportViewSet

router = DefaultRouter()
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'import', ImportViewSet, basename='import')

urlpatterns = [
    path('api/', include(router.urls)),
]