from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from funcionarios.models import Funcionario
from autenticacao.models import UserProfile


class Command(BaseCommand):
    help = 'Sincroniza funcionários existentes criando usuários Django para aqueles que não possuem.'

    def handle(self, *args, **options):
        funcionarios_sem_usuario = Funcionario.objects.filter(
            user_profile__isnull=True
        )

        if not funcionarios_sem_usuario.exists():
            self.stdout.write(self.style.SUCCESS('[OK] Todos os funcionários já possuem usuários Django.'))
            return

        contador = 0
        for funcionario in funcionarios_sem_usuario:
            email = funcionario.email
            username = email.split('@')[0]

            # Garante unicidade do username
            contador_username = 1
            username_base = username
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{contador_username}"
                contador_username += 1

            # Cria o usuário
            try:
                password = get_random_string(12)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=funcionario.nome.split()[0],
                    last_name=' '.join(funcionario.nome.split()[1:]) if len(funcionario.nome.split()) > 1 else '',
                    password=password
                )

                # Cria o perfil
                UserProfile.objects.create(
                    user=user,
                    funcionario=funcionario,
                    setor=funcionario.id_departamento,
                    is_gerente=False,
                    primeiro_acesso=True
                )

                self.stdout.write(f'[+] {funcionario.nome} -> {username}')
                contador += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'[-] Erro ao criar usuário para {funcionario.nome}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n[OK] {contador} usuario(s) sincronizado(s) com sucesso!')
        )
