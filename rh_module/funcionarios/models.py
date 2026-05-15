from django.db import models
from departamentos.models import Departamento
from cargo.models import Cargo


class Funcionario(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('afastado', 'Afastado'),
    ]

    id_funcionario = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=11, unique=True)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    data_admissao = models.DateTimeField()
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ativo')
    id_cargo = models.ForeignKey(
        Cargo,
        on_delete=models.PROTECT,
        related_name='funcionarios',
        db_column='id_cargo'
    )
    id_departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name='funcionarios',
        db_column='id_departamento'
    )

    class Meta:
        db_table = 'funcionarios'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.cpf})'