# cargo/views.py
from drf_spectacular.utils import extend_schema_view, extend_schema

from rest_framework import viewsets, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cargo
from .serializers import CargoSerializer
from departamentos.models import Departamento
from funcionarios.services import (
    FuncionariosAPIError,
    cargo_to_dict,
    listar_cargos,
    listar_funcionarios,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Cargos"],
        summary="Listar cargos",
        description=(
            "Retorna a lista paginada de todos os cargos cadastrados.\n\n"
            "**Filtros disponíveis:**\n"
            "- `id_departamento` – filtra pelo ID do departamento\n"
            "- `nivel` – filtra pelo nível hierárquico do cargo\n\n"
            "**Busca:** campo `search` pesquisa em `nome` e `descricao`.\n\n"
            "**Ordenação:** parâmetro `ordering` aceita `nome` e `nivel`."
        ),
    ),
    create=extend_schema(
        tags=["Cargos"],
        summary="Criar cargo",
        description="Cadastra um novo cargo vinculado a um departamento.",
    ),
    retrieve=extend_schema(
        tags=["Cargos"],
        summary="Detalhar cargo",
        description="Retorna os dados completos de um cargo pelo seu ID.",
    ),
    update=extend_schema(
        tags=["Cargos"],
        summary="Atualizar cargo (PUT)",
        description="Substitui todos os campos de um cargo existente.",
    ),
    partial_update=extend_schema(
        tags=["Cargos"],
        summary="Atualizar cargo parcialmente (PATCH)",
        description="Atualiza apenas os campos informados no corpo da requisição.",
    ),
    destroy=extend_schema(
        tags=["Cargos"],
        summary="Excluir cargo",
        description=(
            "Remove permanentemente um cargo.\n\n"
            "> **Atenção:** não é possível excluir um cargo com funcionários vinculados."
        ),
    ),
)
class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.select_related('id_departamento').all()
    serializer_class = CargoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id_departamento', 'nivel']
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'nivel']

    def list(self, request, *args, **kwargs):
        try:
            cargos = listar_cargos(params=request.query_params)
            return Response([cargo_to_dict(cargo) for cargo in cargos])
        except FuncionariosAPIError:
            return super().list(request, *args, **kwargs)


# ── Views web (templates Django) — sem alterações ─────────────────────────────

@login_required
def cargo_list(request):
    search = request.GET.get('search', '')
    departamento_id = request.GET.get('departamento', '')

    api_source = False
    api_error = None

    try:
        funcionarios = listar_funcionarios()
        cargos = listar_cargos(funcionarios=funcionarios)
        departamentos = sorted(
            {cargo.id_departamento.id_departamento: cargo.id_departamento for cargo in cargos}.values(),
            key=lambda dep: dep.nome,
        )
        api_source = True

        if search:
            termo = search.lower()
            cargos = [
                cargo for cargo in cargos
                if termo in cargo.nome.lower()
                or termo in (cargo.descricao or '').lower()
            ]

        if departamento_id:
            cargos = [
                cargo for cargo in cargos
                if str(cargo.id_departamento.id_departamento) == str(departamento_id)
            ]

        cargos = sorted(cargos, key=lambda cargo: cargo.nome)
    except FuncionariosAPIError as exc:
        api_error = str(exc)
        cargos = Cargo.objects.select_related('id_departamento').all()

        if search:
            cargos = cargos.filter(nome__icontains=search) | \
                     cargos.filter(descricao__icontains=search)

        if departamento_id:
            cargos = cargos.filter(id_departamento=departamento_id)

        departamentos = Departamento.objects.all()

    return render(request, 'cargo/list.html', {
        'cargos': cargos,
        'departamentos': departamentos,
        'search': search,
        'departamento_id': departamento_id,
        'api_source': api_source,
        'api_error': api_error,
    })


@login_required
def cargo_detail(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    return render(request, 'cargo/detail.html', {
        'object': cargo,
    })


@login_required
def cargo_create(request, departamento_id=None):
    if not request.user.profile.is_gerente:
        messages.error(request, 'Apenas gerentes podem cadastrar cargos.')
        return redirect('cargo_list')

    departamento = None
    if departamento_id:
        departamento = get_object_or_404(Departamento, pk=departamento_id)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        nivel = request.POST.get('nivel', '')
        dept_id = request.POST.get('id_departamento', '')

        if not nome or not dept_id or not nivel:
            messages.error(request, 'Nome, departamento e nível são obrigatórios.')
            return render(request, 'cargo/form.html', {
                'departamentos': Departamento.objects.all(),
                'departamento': departamento,
            })

        try:
            Cargo.objects.create(
                nome=nome,
                descricao=descricao,
                nivel=int(nivel),
                id_departamento_id=dept_id
            )
            messages.success(request, f'Cargo {nome} criado com sucesso!')
            return redirect('cargo_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar cargo: {str(e)}')
            return render(request, 'cargo/form.html', {
                'departamentos': Departamento.objects.all(),
                'departamento': departamento,
            })

    return render(request, 'cargo/form.html', {
        'departamentos': Departamento.objects.all(),
        'departamento': departamento,
    })


@login_required
def cargo_edit(request, pk):
    if not request.user.profile.is_gerente:
        messages.error(request, 'Apenas gerentes podem editar cargos.')
        return redirect('cargo_list')

    cargo = get_object_or_404(Cargo, pk=pk)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        nivel = request.POST.get('nivel', '')
        dept_id = request.POST.get('id_departamento', '')

        if not nome or not dept_id or not nivel:
            messages.error(request, 'Nome, departamento e nível são obrigatórios.')
            return render(request, 'cargo/form.html', {
                'object': cargo,
                'departamentos': Departamento.objects.all(),
            })

        try:
            cargo.nome = nome
            cargo.descricao = descricao
            cargo.nivel = int(nivel)
            cargo.id_departamento_id = dept_id
            cargo.save()
            messages.success(request, f'Cargo {nome} atualizado com sucesso!')
            return redirect('cargo_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar cargo: {str(e)}')
            return render(request, 'cargo/form.html', {
                'object': cargo,
                'departamentos': Departamento.objects.all(),
            })

    return render(request, 'cargo/form.html', {
        'object': cargo,
        'departamentos': Departamento.objects.all(),
    })


@login_required
def cargo_delete(request, pk):
    if not request.user.profile.is_gerente:
        messages.error(request, 'Apenas gerentes podem excluir cargos.')
        return redirect('cargo_list')

    cargo = get_object_or_404(Cargo, pk=pk)

    if request.method == 'POST':
        try:
            nome = cargo.nome
            cargo.delete()
            messages.success(request, f'Cargo {nome} excluído com sucesso!')
        except Exception:
            messages.error(request, 'Não é possível excluir um cargo com funcionários vinculados.')
        return redirect('cargo_list')

    return render(request, 'cargo/confirm_delete.html', {'object': cargo})
