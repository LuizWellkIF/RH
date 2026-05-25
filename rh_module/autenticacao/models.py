from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    funcionario     = models.OneToOneField(
        'funcionarios.Funcionario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='user_profile'
    )
    setor           = models.ForeignKey(
        'departamentos.Departamento',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usuarios'
    )
    is_gerente      = models.BooleanField(default=False)
    primeiro_acesso = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.setor})'

    @property
    def is_rh(self):
        return self.setor and self.setor.sigla.lower() == 'rh'