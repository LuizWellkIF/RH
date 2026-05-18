from django.urls import path
from . import views

urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Usuários do sistema (somente gerente)
    path('usuarios/', views.listar_usuarios_view, name='listar_usuarios'),
    path('usuarios/novo/', views.criar_usuario_view, name='criar_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario_view, name='editar_usuario'),
    path('usuarios/<int:pk>/desativar/', views.desativar_usuario_view, name='desativar_usuario'),

    # Senha
    path('alterar-senha/', views.alterar_senha_view, name='alterar_senha'),
]