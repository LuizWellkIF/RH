from django.urls import path

from . import views


urlpatterns = [
    # Tela de bate ponto (principal)
    path('', views.bate_ponto_view, name='ponto_registros'),

    # Tela de consultas consumindo endpoints do DRF
    path('consultas/', views.ponto_consultas_view, name='ponto_consultas'),
]
