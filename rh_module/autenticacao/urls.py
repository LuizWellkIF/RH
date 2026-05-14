from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('usuarios/', views.listar_usuarios_view, name='listar_usuarios'),
    path('usuarios/novo/', views.criar_usuario_view, name='criar_usuario'),
    path('alterar-senha/', views.alterar_senha_view, name='alterar_senha'),
]