from django.urls import path
from . import views

urlpatterns = [
    path('', views.ferias_list, name='ferias_list'),
    path('<int:pk>/', views.ferias_detail, name='ferias_detail'),
    path('novo/', views.ferias_create, name='ferias_create'),
    path('<int:pk>/editar/', views.ferias_edit, name='ferias_edit'),
    path('<int:pk>/excluir/', views.ferias_delete, name='ferias_delete'),
    path('<int:pk>/aprovar/', views.ferias_aprovar, name='ferias_aprovar'),
    path('<int:pk>/recusar/', views.ferias_recusar, name='ferias_recusar'),
]
