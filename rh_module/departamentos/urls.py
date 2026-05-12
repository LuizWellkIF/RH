from rest_framework.routers import DefaultRouter
from .views import DepartamentoViewSet

'''
Configuração das rotas para o módulo de departamentos, utilizando o DefaultRouter do Django REST Framework para criar as rotas automaticamente com base no DepartamentoViewSet.
A rota base para os departamentos será 'api/v1/departamentos/', conforme definido no core/urls.py, e as rotas específicas para cada ação (list, create, retrieve, update, delete) serão geradas automaticamente pelo router.
'''
router = DefaultRouter()
router.register(r'', DepartamentoViewSet, basename='departamentos')

urlpatterns = router.urls