# departamentos/views.py
from drf_spectacular.utils import extend_schema_view, extend_schema

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Departamento
from .serializers import DepartamentoSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Departamentos"],
        summary="Listar departamentos",
        description=(
            "Retorna a lista de todos os departamentos cadastrados.\n\n"
            "**Busca:** campo `search` pesquisa em `nome` e `sigla`.\n\n"
            "**Ordenação:** parâmetro `ordering` aceita `nome` e `sigla`."
        ),
    ),
    create=extend_schema(
        tags=["Departamentos"],
        summary="Criar departamento",
        description="Cadastra um novo departamento. A sigla deve ser única no sistema.",
    ),
    retrieve=extend_schema(
        tags=["Departamentos"],
        summary="Detalhar departamento",
        description="Retorna os dados completos de um departamento pelo seu ID.",
    ),
    update=extend_schema(
        tags=["Departamentos"],
        summary="Atualizar departamento (PUT)",
        description="Substitui todos os campos de um departamento existente.",
    ),
    partial_update=extend_schema(
        tags=["Departamentos"],
        summary="Atualizar departamento parcialmente (PATCH)",
        description="Atualiza apenas os campos informados no corpo da requisição.",
    ),
    destroy=extend_schema(
        tags=["Departamentos"],
        summary="Excluir departamento",
        description=(
            "Remove permanentemente um departamento.\n\n"
            "> **Atenção:** não é possível excluir um departamento com "
            "funcionários ou cargos vinculados."
        ),
    ),
)
class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'sigla']
    ordering_fields = ['nome', 'sigla']

    @extend_schema(
        tags=["Departamentos"],
        summary="Listar funcionários do departamento",
        description=(
            "Retorna todos os funcionários vinculados ao departamento informado.\n\n"
            "O ID do departamento é passado na URL (parâmetro `{id}`)."
        ),
    )
    @action(detail=True, methods=['get'], url_path='funcionarios')
    def listar_funcionarios(self, request, pk=None):
        departamento = self.get_object()

        from funcionarios.models import Funcionario
        from funcionarios.serializers import FuncionarioSerializer

        funcionarios = Funcionario.objects.filter(id_departamento=departamento)
        serializer = FuncionarioSerializer(funcionarios, many=True)

        return Response(serializer.data)


# ── Views web (templates Django) — sem alterações ─────────────────────────────

@login_required
def departamento_list(request):
    search = request.GET.get('search', '')
    departamentos = Departamento.objects.all()
    if search:
        departamentos = departamentos.filter(nome__icontains=search) | \
                        departamentos.filter(sigla__icontains=search)
    return render(request, 'departamentos/list.html', {
        'departamentos': departamentos,
    })


@login_required
def departamento_detail(request, pk):
    departamento = get_object_or_404(Departamento, pk=pk)
    return render(request, 'departamentos/detail.html', {
        'object': departamento,
    })


@login_required
def departamento_create(request):
    if not request.user.profile.is_gerente:
        messages.error(request, 'Apenas gerentes podem cadastrar departamentos.')
        return redirect('departamento_list')

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        sigla = request.POST.get('sigla', '').strip().upper()

        if not nome or not sigla:
            messages.error(request, 'Nome e sigla são obrigatórios.')
            return render(request, 'departamentos/form.html')

        if Departamento.objects.filter(sigla=sigla).exists():
            messages.error(request, f'Já existe um departamento com a sigla "{sigla}".')
            return render(request, 'departamentos/form.html')

        Departamento.objects.create(nome=nome, sigla=sigla)
        messages.success(request, f'Departamento {sigla} criado com sucesso!')
        return redirect('departamento_list')

    return render(request, 'departamentos/form.html')


@login_required
def departamento_edit(request, pk):
    if not request.user.profile.is_gerente:
        messages.error(request, 'Apenas gerentes podem editar departamentos.')
        return redirect('departamento_list')

    departamento = get_object_or_404(Departamento, pk=pk)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        sigla = request.POST.get('sigla', '').strip().upper()

        if not nome or not sigla:
            messages.error(request, 'Nome e sigla são obrigatórios.')
            return render(request, 'departamentos/form.html', {'object': departamento})

        if Departamento.objects.filter(sigla=sigla).exclude(pk=pk).exists():
            messages.error(request, f'Já existe um departamento com a sigla "{sigla}".')
            return render(request, 'departamentos/form.html', {'object': departamento})

        departamento.nome = nome
        departamento.sigla = sigla
        departamento.save()
        messages.success(request, f'Departamento {sigla} atualizado com sucesso!')
        return redirect('departamento_list')

    return render(request, 'departamentos/form.html', {'object': departamento})


@login_required
def departamento_delete(request, pk):
    if not request.user.profile.is_gerente:
        messages.error(request, 'Apenas gerentes podem excluir departamentos.')
        return redirect('departamento_list')

    departamento = get_object_or_404(Departamento, pk=pk)

    if request.method == 'POST':
        try:
            sigla = departamento.sigla
            departamento.delete()
            messages.success(request, f'Departamento {sigla} excluído com sucesso!')
        except Exception:
            messages.error(request, 'Não é possível excluir um departamento com funcionários ou cargos vinculados.')
        return redirect('departamento_list')

    return render(request, 'departamentos/confirm_delete.html', {'object': departamento})