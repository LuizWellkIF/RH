from django.db import models
from funcionarios.models import Funcionario


class SolicitacaoFerias(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('recusada', 'Recusada'),
    ]

    id_solicitacao = models.BigAutoField(primary_key=True)
    id_funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='solicitacoes_ferias',
        db_column='id_funcionario'
    )
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    observacao = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'solicitacao_ferias'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f'{self.id_funcionario.nome} — {self.data_inicio} a {self.data_fim} ({self.status})'

    @property
    def dias_solicitados(self):
        return (self.data_fim - self.data_inicio).days + 1