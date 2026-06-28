# funcionarios/views.py
from drf_spectacular.utils import extend_schema_view, extend_schema

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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
from .services import (
    FuncionariosAPIError,
    funcionario_to_dict,
    listar_cargos,
    listar_funcionarios,
    preencher_cargos_funcionarios,
)


def _criar_usuario_para_funcionario(funcionario: Funcionario) -> User:
    if UserProfile.objects.filter(funcionario=funcionario).exists():
        return UserProfile.objects.get(funcionario=funcionario).user
    """Cria um usuário Django para um funcionário com base no email."""
    email = funcionario.email
    username = email.split('@')[0]

    contador = 1
    username_base = username
    while User.objects.filter(username=username).exists():
        username = f"{username_base}{contador}"
        contador += 1

    password = get_random_string(12)
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=funcionario.nome.split()[0],
        last_name=' '.join(funcionario.nome.split()[1:]) if len(funcionario.nome.split()) > 1 else '',
        password=password
    )

    UserProfile.objects.create(
        user=user,
        funcionario=funcionario,
        primeiro_acesso=True
    )

    return user


@extend_schema_view(
    list=extend_schema(
        tags=["Funcionários"],
        summary="Listar funcionários",
        description=(
            "Retorna a lista paginada de todos os funcionários cadastrados.\n\n"
            "**Filtros disponíveis:**\n"
            "- `status` – filtra pelo status do funcionário (ex: `ativo`, `inativo`)\n"
            "- `id_departamento` – filtra pelo ID do departamento\n"
            "- `id_cargo` – filtra pelo ID do cargo\n\n"
            "**Busca:** campo `search` pesquisa em `nome`, `cpf` e `email`.\n\n"
            "**Ordenação:** parâmetro `ordering` aceita `nome`, `data_admissao` e `salario`."
        ),
    ),
    create=extend_schema(
        tags=["Funcionários"],
        summary="Cadastrar funcionário",
        description="Cadastra um novo funcionário no sistema.",
    ),
    retrieve=extend_schema(
        tags=["Funcionários"],
        summary="Detalhar funcionário",
        description="Retorna os dados completos de um funcionário pelo seu ID.",
    ),
    update=extend_schema(
        tags=["Funcionários"],
        summary="Atualizar funcionário (PUT)",
        description="Substitui todos os campos de um funcionário existente.",
    ),
    partial_update=extend_schema(
        tags=["Funcionários"],
        summary="Atualizar funcionário parcialmente (PATCH)",
        description="Atualiza apenas os campos informados no corpo da requisição.",
    ),
    destroy=extend_schema(
        tags=["Funcionários"],
        summary="Excluir funcionário",
        description=(
            "Remove permanentemente um funcionário e seu usuário de acesso vinculado.\n\n"
            "> **Atenção:** a exclusão é irreversível e remove todos os registros associados."
        ),
    ),
)
class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.select_related(
        'id_cargo', 'id_departamento'
    ).all()
    serializer_class = FuncionarioSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'id_departamento', 'id_cargo']
    search_fields = ['nome', 'cpf', 'email']
    ordering_fields = ['nome', 'data_admissao', 'salario']

    def list(self, request, *args, **kwargs):
        try:
            funcionarios = listar_funcionarios(params=request.query_params)
            cargos = listar_cargos()
            preencher_cargos_funcionarios(funcionarios, cargos)
            return Response([funcionario_to_dict(funcionario) for funcionario in funcionarios])
        except FuncionariosAPIError:
            return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Funcionários"],
        summary="Relatório de funcionários",
        description=(
            "Retorna um resumo estatístico dos funcionários cadastrados.\n\n"
            "**Dados retornados:**\n"
            "- `por_departamento` – contagem de funcionários agrupados por departamento\n"
            "- `por_status` – contagem agrupada por status (ativo, inativo etc.)\n"
            "- `total_geral` – total absoluto de funcionários cadastrados"
        ),
    )
    @action(detail=False, methods=['get'], url_path='relatorio')
    def relatorio(self, request):
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


# ── Views web (templates Django) — sem alterações ─────────────────────────────

@login_required
def funcionarios_list_view(request):
    q = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    departamento_id = (request.GET.get('departamento') or '').strip()
    cargo_id = (request.GET.get('cargo') or '').strip()

    api_source = False
    api_error = None

    try:
        funcionarios = listar_funcionarios()
        cargos = listar_cargos(funcionarios=funcionarios)
        preencher_cargos_funcionarios(funcionarios, cargos)
        departamentos = sorted(
            {f.id_departamento.id_departamento: f.id_departamento for f in funcionarios}.values(),
            key=lambda dep: dep.nome,
        )
        api_source = True

        if q:
            termo = q.lower()
            funcionarios = [
                funcionario for funcionario in funcionarios
                if termo in funcionario.nome.lower()
                or termo in funcionario.cpf.lower()
                or termo in funcionario.email.lower()
            ]

        if status:
            funcionarios = [
                funcionario for funcionario in funcionarios
                if funcionario.status == status
            ]

        if departamento_id.isdigit():
            funcionarios = [
                funcionario for funcionario in funcionarios
                if str(funcionario.id_departamento.id_departamento) == departamento_id
            ]

        if cargo_id.isdigit():
            funcionarios = [
                funcionario for funcionario in funcionarios
                if str(funcionario.id_cargo.id_cargo) == cargo_id
            ]

        funcionarios = sorted(funcionarios, key=lambda funcionario: funcionario.nome)
        cargos = sorted(cargos, key=lambda cargo: cargo.nome)
    except FuncionariosAPIError as exc:
        api_error = str(exc)
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

        funcionarios = queryset.order_by('nome')
        departamentos = Departamento.objects.order_by('nome')
        cargos = Cargo.objects.select_related('id_departamento').order_by('nome')

    context = {
        'funcionarios': funcionarios,
        'departamentos': departamentos,
        'cargos': cargos,
        'q': q,
        'status': status,
        'departamento_id': departamento_id,
        'cargo_id': cargo_id,
        'api_source': api_source,
        'api_error': api_error,
    }
    return render(request, 'funcionarios/list.html', context)


@login_required
def funcionario_create_view(request):
    form = FuncionarioForm(request.POST or None)
    usuario_criado = None
    senha_gerada = None

    if request.method == 'POST' and form.is_valid():
        funcionario = form.save()

        try:
            usuario_criado = _criar_usuario_para_funcionario(funcionario)
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
            nome_funcionario = funcionario.nome
            funcionario.delete()
            messages.success(request, f'Funcionário "{nome_funcionario}" removido com sucesso!')
            return redirect('funcionarios_list')
        except ProtectedError:
            messages.error(request, 'Não foi possível excluir: há registros vinculados a este funcionário.')
            return redirect('funcionarios_list')

    return render(request, 'funcionarios/confirm_delete.html', {
        'funcionario': funcionario,
    })
