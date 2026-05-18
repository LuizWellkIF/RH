from django.contrib import admin
from .models import SolicitacaoFerias


@admin.register(SolicitacaoFerias)
class SolicitacaoFeriasAdmin(admin.ModelAdmin):
    list_display = ['id_solicitacao', 'id_funcionario', 'data_inicio', 'data_fim', 'status']
    list_filter = ['status']
    search_fields = ['id_funcionario__nome']
    ordering = ['-data_solicitacao']