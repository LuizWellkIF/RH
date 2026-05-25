from django.urls import path
from . import views

urlpatterns = [
    path('', views.cargo_list, name='cargo_list'),
    path('novo/', views.cargo_create, name='cargo_create'),
    path('novo/<int:departamento_id>/', views.cargo_create, name='cargo_create_departamento'),
    path('<int:pk>/', views.cargo_detail, name='cargo_detail'),
    path('<int:pk>/editar/', views.cargo_edit, name='cargo_edit'),
    path('<int:pk>/deletar/', views.cargo_delete, name='cargo_delete'),
]
