from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.departamento_list,   name='departamento_list'),
    path('<int:pk>/',           views.departamento_detail, name='departamento_detail'),
    path('novo/',               views.departamento_create, name='departamento_create'),
    path('<int:pk>/editar/',    views.departamento_edit,   name='departamento_edit'),
    path('<int:pk>/excluir/',   views.departamento_delete, name='departamento_delete'),
]