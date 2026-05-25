from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from autenticacao.models import UserProfile
from .models import Funcionario


@receiver(post_save, sender=Funcionario)
def criar_usuario_funcionario(sender, instance, created, **kwargs):
    if not created:
        return

    # Gera username: "Ana Paula Souza" → "ana.souza"
    nome_parts = instance.nome.lower().split()
    primeiro   = nome_parts[0]
    ultimo     = nome_parts[-1] if len(nome_parts) > 1 else nome_parts[0]
    username   = f'{primeiro}.{ultimo}'

    # Garante unicidade
    username_final = username
    contador = 1
    while User.objects.filter(username=username_final).exists():
        username_final = f'{username}{contador}'
        contador += 1

    # Senha temporária: primeiro.ultimo123
    senha_padrao = f'{primeiro}.{ultimo}123'

    user = User.objects.create_user(
        username=username_final,
        email=instance.email,
        password=senha_padrao,
        first_name=primeiro.capitalize(),
        last_name=' '.join(nome_parts[1:]).title(),
    )

    UserProfile.objects.create(
        user=user,
        funcionario=instance,
        setor=instance.id_departamento,
        is_gerente=False,
        primeiro_acesso=True,
    )


@receiver(post_delete, sender=Funcionario)
def remover_usuario_funcionario(sender, instance, **kwargs):
    if hasattr(instance, 'user_profile') and instance.user_profile:
        instance.user_profile.user.delete()