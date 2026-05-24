from django.urls import path
from . import views

urlpatterns = [
    path('', views.funcionarios_list_view, name='funcionarios_list'),
    path('novo/', views.funcionario_create_view, name='funcionario_create'),
    path('<int:pk>/editar/', views.funcionario_edit_view, name='funcionario_edit'),
    path('<int:pk>/excluir/', views.funcionario_delete_view, name='funcionario_delete'),
]
