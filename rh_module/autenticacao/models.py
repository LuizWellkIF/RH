from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    CARGO_RH_CHOICES = [
        ('diretor', 'Diretor de RH'),
        ('gerente', 'Gerente de RH'),
        ('coordenador', 'Coordenador de RH'),
        ('analista', 'Analista de RH'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    funcionario = models.OneToOneField(
        'funcionarios.Funcionario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profile'
    )
    cargo_rh = models.CharField(max_length=20, choices=CARGO_RH_CHOICES)

    class Meta:
        db_table = 'user_profile'
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuário'

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.get_cargo_rh_display()})'
    
    @property
    def is_diretor(self):
        return self.cargo_rh == 'diretor'

    @property
    def is_gerente(self):
        return self.cargo_rh == 'gerente'

    @property
    def is_coordenador(self):
        return self.cargo_rh == 'coordenador'

    @property
    def is_analista(self):
        return self.cargo_rh == 'analista'