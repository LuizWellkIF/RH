"""
URL configuration for rh_module project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

'''
Adiciona aqui as rotas do admins e da API de cada módulo, conforme a rota de departamento.
Por enquanto, só faremos as rotas de API para consumir os dados no futuro.
Os templates e views para o frontend serão feitos depois, e as rotas para o frontend serão adicionadas aqui também.
'''
urlpatterns = [

    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard'), name='home'),
    path('', include('autenticacao.urls')),
    path('api/v1/departamentos/', include('departamentos.urls')),
    path('api/v1/cargo/', include('cargo.urls')),
    path('api/v1/funcionarios/', include('funcionarios.urls')),
    path('api/v1/ponto/', include('ponto.urls')),
    path('api/v1/ferias/', include('ferias.urls')),
]
