from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cargo
from .serializers import CargoSerializer
from departamentos.models import Departamento


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.select_related('id_departamento').all()
    serializer_class = CargoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id_departamento', 'nivel']
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'nivel']


@login_required
def cargo_list(request):
    search = request.GET.get('search', '')
    departamento_id = request.GET.get('departamento', '')

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