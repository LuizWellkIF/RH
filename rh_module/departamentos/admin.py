from django.contrib import admin
from .models import Departamento
# Register your models here.

'''
Admin para o modelo Departamento, permitindo a visualização e gerenciamento dos departamentos no painel administrativo do Django.
O list_display define os campos que serão exibidos na lista, de acordo com o BD. O search_fields permite a busca por nome e sigla,
e o ordering define a ordenação padrão por nome.
'''
@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['id_departamento', 'sigla', 'nome']
    search_fields = ['nome', 'sigla']
    ordering = ['nome']