from django.contrib import admin
from .models import Departamento
# Register your models here.

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['id_departamento', 'sigla', 'nome']
    search_fields = ['nome', 'sigla']
    ordering = ['nome']