from django.db import models
from departamentos.models import Departamento


class Cargo(models.Model):
    NIVEL_CHOICES = [
        (1, 'Júnior'),
        (2, 'Pleno'),
        (3, 'Sênior'),
        (4, 'Coordenador'),
        (5, 'Gerente'),
        (6, 'Diretor'),
    ]

    id_cargo = models.BigAutoField(primary_key=True)
    id_departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name='cargos',
        db_column='id_departamento'
    )
    nome = models.CharField(max_length=255)
    descricao = models.TextField(null=True, blank=True)
    nivel = models.SmallIntegerField(choices=NIVEL_CHOICES, null=True, blank=True)

    class Meta:
        db_table = 'cargo'
        ordering = ['id_departamento', 'nivel', 'nome']

    def __str__(self):
        return f'{self.nome} ({self.get_nivel_display()})'