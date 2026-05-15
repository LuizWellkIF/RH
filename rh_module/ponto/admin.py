from django.contrib import admin
from .models import RegistroPonto


@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = ['id_registro', 'id_funcionario', 'tipo', 'data_hora']
    list_filter = ['tipo', 'data_hora']
    search_fields = ['id_funcionario__nome']
    ordering = ['-data_hora']   