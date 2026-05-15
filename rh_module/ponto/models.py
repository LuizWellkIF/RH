from django.db import models
from funcionarios.models import Funcionario


class RegistroPonto(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('pausa', 'Pausa'),
    ]

    id_registro = models.BigAutoField(primary_key=True)
    id_funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='registros_ponto',
        db_column='id_funcionario'
    )
    data_hora = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    observacao = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'registros_ponto'
        ordering = ['-data_hora']

    def __str__(self):
        return f'{self.id_funcionario.nome} — {self.tipo} em {self.data_hora:%d/%m/%Y %H:%M}'