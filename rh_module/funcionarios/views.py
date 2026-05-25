from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import get_password_validators
from django.core.management import call_command
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, request, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from cargo.models import Cargo
from departamentos.models import Departamento
from autenticacao.models import UserProfile
from .models import Funcionario
from .serializers import FuncionarioSerializer
from .forms import FuncionarioForm


def _criar_usuario_para_funcionario(funcionario: Funcionario) -> User:
    if UserProfile.objects.filter(funcionario=funcionario).exists():
        return UserProfile.objects.get(funcionario=funcionario).user
    """Cria um usuário Django para um funcionário com base no email."""
    email = funcionario.email
    username = email.split('@')[0]

    # Garante unicidade do username
    contador = 1
    username_base = username
    while User.objects.filter(username=username).exists():
        username = f"{username_base}{contador}"
        contador += 1

    # Cria o usuário com senha aleatória (será alterada no primeiro acesso)
    password = get_random_string(12)
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=funcionario.nome.split()[0],
        last_name=' '.join(funcionario.nome.split()[1:]) if len(funcionario.nome.split()) > 1 else '',
        password=password
    )

    # Cria o perfil do usuário
    UserProfile.objects.create(
        user=user,
        funcionario=funcionario,
        primeiro_acesso=True
    )

    return user


class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.select_related(
        'id_cargo', 'id_departamento'
    ).all()
    serializer_class = FuncionarioSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'id_departamento', 'id_cargo']
    search_fields = ['nome', 'cpf', 'email']
    ordering_fields = ['nome', 'data_admissao', 'salario']

    @action(detail=False, methods=['get'], url_path='relatorio')
    def relatorio(self, request):
        """Retorna contagem de funcionários agrupados por departamento e status."""
        por_departamento = (
            Funcionario.objects
            .values('id_departamento__nome')
            .annotate(total=Count('id_funcionario'))
            .order_by('id_departamento__nome')
        )
        por_status = (
            Funcionario.objects
            .values('status')
            .annotate(total=Count('id_funcionario'))
        )
        return Response({
            'por_departamento': list(por_departamento),
            'por_status': list(por_status),
            'total_geral': Funcionario.objects.count(),
        })


# ── Views Web (templates) ─────────────────────────────────────────────────────

@login_required
def funcionarios_list_view(request):
    q = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    departamento_id = (request.GET.get('departamento') or '').strip()
    cargo_id = (request.GET.get('cargo') or '').strip()

    queryset = Funcionario.objects.select_related('id_cargo', 'id_departamento').all()

    if q:
        queryset = queryset.filter(
            Q(nome__icontains=q)
            | Q(cpf__icontains=q)
            | Q(email__icontains=q)
        )

    if status:
        queryset = queryset.filter(status=status)

    if departamento_id.isdigit():
        queryset = queryset.filter(id_departamento_id=int(departamento_id))

    if cargo_id.isdigit():
        queryset = queryset.filter(id_cargo_id=int(cargo_id))

    context = {
        'funcionarios': queryset.order_by('nome'),
        'departamentos': Departamento.objects.order_by('nome'),
        'cargos': Cargo.objects.select_related('id_departamento').order_by('nome'),
        'q': q,
        'status': status,
        'departamento_id': departamento_id,
        'cargo_id': cargo_id,
    }
    return render(request, 'funcionarios/list.html', context)


@login_required
def funcionario_create_view(request):
    form = FuncionarioForm(request.POST or None)
    usuario_criado = None
    senha_gerada = None

    if request.method == 'POST' and form.is_valid():
        funcionario = form.save()

        # Cria usuário Django automaticamente
        try:
            usuario_criado = _criar_usuario_para_funcionario(funcionario)
            email = funcionario.email
            username = email.split('@')[0]

            # Gera senha aleatória
            senha_gerada = get_random_string(12)
            usuario_criado.set_password(senha_gerada)
            usuario_criado.save()

            messages.success(
                request,
                f'Funcionário "{funcionario.nome}" criado com sucesso!'
            )
        except Exception as e:
            messages.warning(
                request,
                f'Funcionário "{funcionario.nome}" criado, '
                f'mas houve erro ao criar usuário: {str(e)}'
            )

        return render(request, 'funcionarios/form.html', {
            'form': form,
            'mode': 'create',
            'usuario_criado': usuario_criado,
            'senha_gerada': senha_gerada,
        })

    return render(request, 'funcionarios/form.html', {
        'form': form,
        'mode': 'create',
    })


@login_required
def funcionario_edit_view(request, pk: int):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    form = FuncionarioForm(request.POST or None, instance=funcionario)

    if request.method == 'POST' and form.is_valid():
        funcionario = form.save()
        messages.success(request, f'Funcionário "{funcionario.nome}" atualizado com sucesso!')
        return redirect('funcionarios_list')

    return render(request, 'funcionarios/form.html', {
        'form': form,
        'funcionario': funcionario,
        'mode': 'edit',
    })


@login_required
def funcionario_delete_view(request, pk: int):
    funcionario = get_object_or_404(Funcionario, pk=pk)

    if request.method == 'POST':
        try:
            nome_funcionario = funcionario.nome  # Salva antes de deletar
            funcionario.delete()  # Deleta func + cascata deleta user + profile
            messages.success(request, f'Funcionário "{nome_funcionario}" removido com sucesso!')
            return redirect('funcionarios_list')
        except ProtectedError:
            messages.error(request, 'Não foi possível excluir: há registros vinculados a este funcionário.')
            return redirect('funcionarios_list')

    return render(request, 'funcionarios/confirm_delete.html', {
    'funcionario': funcionario,
    })