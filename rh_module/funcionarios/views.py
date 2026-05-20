from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cargo.models import Cargo
from departamentos.models import Departamento
from .models import Funcionario
from .serializers import FuncionarioSerializer
from .forms import FuncionarioForm


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

    if request.method == 'POST' and form.is_valid():
        funcionario = form.save()
        messages.success(request, f'Funcionário "{funcionario.nome}" criado com sucesso!')
        return redirect('funcionarios_list')

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
            funcionario.delete()
            messages.success(request, f'Funcionário "{funcionario.nome}" removido com sucesso!')
            return redirect('funcionarios_list')
        except ProtectedError:
            messages.error(request, 'Não foi possível excluir: há registros vinculados a este funcionário.')
            return redirect('funcionarios_list')

    return render(request, 'funcionarios/confirm_delete.html', {
        'funcionario': funcionario,
    })