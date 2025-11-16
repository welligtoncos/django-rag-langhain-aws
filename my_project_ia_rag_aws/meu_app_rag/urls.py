from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'produtos', views.ProdutoViewSet, basename='produto')
router.register(r'rag', views.RAGViewSet, basename='rag')

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Rotas dos ViewSets
    path('', include(router.urls)),
]