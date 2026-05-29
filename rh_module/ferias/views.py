from rest_framework import viewsets, filters, status as drf_status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import SolicitacaoFerias
from .serializers import SolicitacaoFeriasSerializer
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from funcionarios.models import Funcionario


def _get_user_profile(user):
    return getattr(user, 'profile', None)


def _get_funcionario_do_usuario(user):
    perfil = _get_user_profile(user)
    if perfil is None:
        return None
    return getattr(perfil, 'funcionario', None)


def _user_is_rh(user):
    perfil = _get_user_profile(user)
    return user.is_superuser or (perfil is not None and perfil.is_rh)


def _user_can_decide_ferias(user):
    if user.is_superuser:
        return True

    if not _user_is_rh(user):
        return False

    funcionario = _get_funcionario_do_usuario(user)
    cargo = getattr(funcionario, 'id_cargo', None)
    return getattr(cargo, 'nivel', None) in (4, 5, 6)


def _validate_periodo_ferias(funcionario, data_inicio, data_fim, instance=None):
    if data_fim <= data_inicio:
        return 'A data de fim deve ser posterior à data de início.'

    if (data_fim - data_inicio).days + 1 < 5:
        return 'O período mínimo de férias é de 5 dias.'

    sobreposicao = SolicitacaoFerias.objects.filter(
        id_funcionario=funcionario,
        status='aprovada',
        data_inicio__lte=data_fim,
        data_fim__gte=data_inicio,
    )
    if instance is not None:
        sobreposicao = sobreposicao.exclude(pk=instance.pk)

    if sobreposicao.exists():
        return 'Já existe férias aprovadas nesse período para este funcionário.'

    return None


class SolicitacaoFeriasViewSet(viewsets.ModelViewSet):
    queryset = SolicitacaoFerias.objects.select_related('id_funcionario').all()
    serializer_class = SolicitacaoFeriasSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['id_funcionario', 'status']
    ordering_fields = ['data_solicitacao', 'data_inicio']

    @action(detail=True, methods=['patch'], url_path='aprovar')
    def aprovar(self, request, pk=None):
        if not _user_can_decide_ferias(request.user):
            return Response(
                {'erro': 'Apenas cargos de nível 4, 5 ou 6 podem aprovar férias.'},
                status=drf_status.HTTP_403_FORBIDDEN
            )

        solicitacao = self.get_object()

        if solicitacao.status != 'pendente':
            return Response(
                {'erro': f'Não é possível aprovar uma solicitação com status "{solicitacao.status}".'},
                status=400
            )

        solicitacao.status = 'aprovada'
        solicitacao.observacao = request.data.get('observacao', solicitacao.observacao)
        solicitacao.save()
        serializer = self.get_serializer(solicitacao)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='recusar')
    def recusar(self, request, pk=None):
        if not _user_can_decide_ferias(request.user):
            return Response(
                {'erro': 'Apenas cargos de nível 4, 5 ou 6 podem recusar férias.'},
                status=drf_status.HTTP_403_FORBIDDEN
            )

        solicitacao = self.get_object()

        if solicitacao.status != 'pendente':
            return Response(
                {'erro': f'Não é possível recusar uma solicitação com status "{solicitacao.status}".'},
                status=400
            )

        solicitacao.status = 'recusada'
        solicitacao.observacao = request.data.get('observacao', solicitacao.observacao)
        solicitacao.save()
        serializer = self.get_serializer(solicitacao)
        return Response(serializer.data)


@login_required
def ferias_list(request):
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    funcionario_id = (request.GET.get('id_funcionario') or '').strip()
    solicitacoes = SolicitacaoFerias.objects.select_related('id_funcionario')
    user_funcionario = _get_funcionario_do_usuario(request.user)
    can_view_all_ferias = _user_is_rh(request.user)
    can_decide_ferias = _user_can_decide_ferias(request.user)

    if can_view_all_ferias:
        solicitacoes = solicitacoes.all()
    else:
        if user_funcionario is None:
            solicitacoes = solicitacoes.none()
        else:
            solicitacoes = solicitacoes.filter(id_funcionario=user_funcionario)

    if search:
        solicitacoes = solicitacoes.filter(
            Q(id_funcionario__nome__icontains=search) |
            Q(id_funcionario__email__icontains=search)
        )

    if status:
        solicitacoes = solicitacoes.filter(status=status)

    if can_view_all_ferias and funcionario_id.isdigit():
        solicitacoes = solicitacoes.filter(id_funcionario_id=int(funcionario_id))

    return render(request, 'ferias/list.html', {
        'solicitacoes': solicitacoes,
        'status_filter': status,
        'funcionario_id_filter': funcionario_id,
        'funcionarios': Funcionario.objects.order_by('nome') if can_view_all_ferias else [],
        'user_funcionario': user_funcionario,
        'can_view_all_ferias': can_view_all_ferias,
        'can_decide_ferias': can_decide_ferias,
    })


@login_required
def ferias_detail(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)

    if not _user_is_rh(request.user):
        funcionario = _get_funcionario_do_usuario(request.user)
        if funcionario is None or solicitacao.id_funcionario != funcionario:
            messages.error(request, 'Você não tem permissão para acessar esta solicitação.')
            return redirect('ferias_list')

    user_funcionario = _get_funcionario_do_usuario(request.user)
    can_decide_ferias = _user_can_decide_ferias(request.user)

    return render(request, 'ferias/detail.html', {
        'object': solicitacao,
        'can_edit': (solicitacao.status == 'pendente' and user_funcionario == solicitacao.id_funcionario),
        'can_delete': (solicitacao.status == 'pendente' and user_funcionario == solicitacao.id_funcionario),
        'can_approve': (can_decide_ferias and solicitacao.status == 'pendente'),
        'can_view_all_ferias': _user_is_rh(request.user),
        'can_decide_ferias': can_decide_ferias,
    })


@login_required
def ferias_create(request):
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        observacao = request.POST.get('observacao', '')

        if not data_inicio or not data_fim:
            messages.error(request, 'Data de início e fim são obrigatórias.')
            return render(request, 'ferias/form.html')

        from datetime import datetime
        try:
            d_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            d_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Formato de data inválido.')
            return render(request, 'ferias/form.html')

        funcionario = _get_funcionario_do_usuario(request.user)
        if funcionario is None:
            messages.error(request, 'Não foi possível criar a solicitação porque seu usuário não está vinculado a um funcionário.')
            return render(request, 'ferias/form.html')

        erro = _validate_periodo_ferias(funcionario, d_inicio, d_fim)
        if erro:
            messages.error(request, erro)
            return render(request, 'ferias/form.html')

        SolicitacaoFerias.objects.create(
            id_funcionario=funcionario,
            data_inicio=d_inicio,
            data_fim=d_fim,
            observacao=observacao,
        )
        messages.success(request, 'Solicitação de férias criada com sucesso!')
        return redirect('ferias_list')

    return render(request, 'ferias/form.html')


@login_required
def ferias_edit(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)

    funcionario = _get_funcionario_do_usuario(request.user)
    if funcionario is None or solicitacao.id_funcionario != funcionario:
        messages.error(request, 'Você só pode editar suas próprias solicitações.')
        return redirect('ferias_list')

    if solicitacao.status != 'pendente':
        messages.error(request, 'Você só pode editar solicitações pendentes.')
        return redirect('ferias_detail', pk=pk)

    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        observacao = request.POST.get('observacao', '')

        if not data_inicio or not data_fim:
            messages.error(request, 'Data de início e fim são obrigatórias.')
            return render(request, 'ferias/form.html', {'object': solicitacao})

        from datetime import datetime
        try:
            d_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            d_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Formato de data inválido.')
            return render(request, 'ferias/form.html', {'object': solicitacao})

        erro = _validate_periodo_ferias(funcionario, d_inicio, d_fim, instance=solicitacao)
        if erro:
            messages.error(request, erro)
            solicitacao.data_inicio = d_inicio
            solicitacao.data_fim = d_fim
            solicitacao.observacao = observacao
            return render(request, 'ferias/form.html', {'object': solicitacao})

        solicitacao.data_inicio = d_inicio
        solicitacao.data_fim = d_fim
        solicitacao.observacao = observacao
        solicitacao.save()
        messages.success(request, 'Solicitação de férias atualizada com sucesso!')
        return redirect('ferias_detail', pk=pk)

    return render(request, 'ferias/form.html', {'object': solicitacao})


@login_required
def ferias_delete(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)

    funcionario = _get_funcionario_do_usuario(request.user)
    if funcionario is None or solicitacao.id_funcionario != funcionario:
        messages.error(request, 'Você só pode deletar suas próprias solicitações.')
        return redirect('ferias_list')

    if solicitacao.status != 'pendente':
        messages.error(request, 'Você só pode deletar solicitações pendentes.')
        return redirect('ferias_detail', pk=pk)

    if request.method == 'POST':
        solicitacao.delete()
        messages.success(request, 'Solicitação de férias excluída com sucesso!')
        return redirect('ferias_list')

    return render(request, 'ferias/confirm_delete.html', {'object': solicitacao})


@login_required
def ferias_aprovar(request, pk):
    if not _user_can_decide_ferias(request.user):
        messages.error(request, 'Apenas cargos de nível 4, 5 ou 6 podem aprovar férias.')
        return redirect('ferias_list')

    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)

    if request.method == 'POST':
        if solicitacao.status != 'pendente':
            messages.error(request, f'Não é possível aprovar uma solicitação com status "{solicitacao.status}".')
            return redirect('ferias_detail', pk=pk)

        observacao = request.POST.get('observacao', solicitacao.observacao)
        solicitacao.status = 'aprovada'
        solicitacao.observacao = observacao
        solicitacao.save()
        messages.success(request, 'Solicitação de férias aprovada com sucesso!')
        return redirect('ferias_detail', pk=pk)

    return render(request, 'ferias/confirm_action.html', {
        'object': solicitacao,
        'action': 'aprovar',
        'action_label': 'Aprovar',
    })


@login_required
def ferias_recusar(request, pk):
    if not _user_can_decide_ferias(request.user):
        messages.error(request, 'Apenas cargos de nível 4, 5 ou 6 podem recusar férias.')
        return redirect('ferias_list')

    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)

    if request.method == 'POST':
        if solicitacao.status != 'pendente':
            messages.error(request, f'Não é possível recusar uma solicitação com status "{solicitacao.status}".')
            return redirect('ferias_detail', pk=pk)

        observacao = request.POST.get('observacao', '')
        solicitacao.status = 'recusada'
        solicitacao.observacao = observacao
        solicitacao.save()
        messages.success(request, 'Solicitação de férias recusada com sucesso!')
        return redirect('ferias_detail', pk=pk)

    return render(request, 'ferias/confirm_action.html', {
        'object': solicitacao,
        'action': 'recusar',
        'action_label': 'Recusar',
    })
