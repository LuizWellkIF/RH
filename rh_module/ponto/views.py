from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import RegistroPonto
from .serializers import RegistroPontoSerializer
from funcionarios.models import Funcionario


class RegistroPontoViewSet(viewsets.ModelViewSet):
    queryset = RegistroPonto.objects.select_related('id_funcionario').all()
    serializer_class = RegistroPontoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['id_funcionario', 'tipo']
    ordering_fields = ['data_hora']

    @action(detail=False, methods=['get'], url_path='espelho')
    def espelho_mensal(self, request):
        """Retorna todos os registros do mês atual de um funcionário."""
        funcionario_id = request.query_params.get('funcionario')
        if not funcionario_id:
            return Response({'erro': 'Informe o parâmetro funcionario.'}, status=400)

        hoje = timezone.now()
        registros = RegistroPonto.objects.filter(
            id_funcionario=funcionario_id,
            data_hora__year=hoje.year,
            data_hora__month=hoje.month,
        ).order_by('data_hora')

        serializer = self.get_serializer(registros, many=True)
        return Response({
            'funcionario_id': funcionario_id,
            'mes': hoje.strftime('%B/%Y'),
            'total_registros': registros.count(),
            'registros': serializer.data,
        })


@login_required
def bate_ponto_view(request):
    """Tela web estilo SouGov para registrar ponto (entrada/saída/entrada/saída) e exibir total trabalhado."""
    server_now = timezone.localtime(timezone.now())
    today = timezone.localdate()

    funcionarios = Funcionario.objects.select_related('id_departamento', 'id_cargo').order_by('nome')
    tipos = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]

    funcionario_id = (request.GET.get('funcionario') or request.POST.get('id_funcionario') or '').strip()
    funcionario = None
    if funcionario_id:
        funcionario = Funcionario.objects.filter(id_funcionario=funcionario_id).first()
        if not funcionario:
            messages.warning(request, 'Funcionário não encontrado. Selecione novamente.')
            funcionario_id = ''

    registros_dia = RegistroPonto.objects.none()
    if funcionario:
        registros_dia = (
            RegistroPonto.objects
            .filter(
                id_funcionario=funcionario,
                data_hora__date=today,
                tipo__in=['entrada', 'saida'],
            )
            .order_by('data_hora')
        )

    entrada1 = None
    saida1 = None
    entrada2 = None
    saida2 = None

    if funcionario:
        entrada1 = registros_dia.filter(tipo='entrada').first()
        if entrada1:
            saida1 = registros_dia.filter(tipo='saida', data_hora__gt=entrada1.data_hora).first()
        else:
            saida1 = registros_dia.filter(tipo='saida').first()

        if saida1:
            entrada2 = registros_dia.filter(tipo='entrada', data_hora__gt=saida1.data_hora).first()

        if entrada2:
            saida2 = registros_dia.filter(tipo='saida', data_hora__gt=entrada2.data_hora).first()

    total_punches = registros_dia.count() if funcionario else 0

    def seconds_between(start_dt, end_dt):
        if not start_dt or not end_dt:
            return 0
        start = timezone.localtime(start_dt)
        end = timezone.localtime(end_dt)
        if end <= start:
            return 0
        return int((end - start).total_seconds())

    total_seconds = 0
    if entrada1:
        total_seconds += seconds_between(entrada1.data_hora, (saida1.data_hora if saida1 else server_now))
    if entrada2:
        total_seconds += seconds_between(entrada2.data_hora, (saida2.data_hora if saida2 else server_now))

    def format_hms(total):
        total = max(0, int(total or 0))
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    can_register = bool(funcionario) and total_punches < 4
    next_tipo = None
    next_label = None

    if funcionario and total_punches >= 4:
        next_label = 'Dia completo'
    elif funcionario:
        last_record = (
            RegistroPonto.objects
            .filter(id_funcionario=funcionario)
            .order_by('-data_hora')
            .first()
        )
        if not last_record:
            next_tipo = 'entrada'
        elif last_record.tipo in ['entrada', 'pausa']:
            next_tipo = 'saida'
        else:
            next_tipo = 'entrada'

        next_label = dict(tipos).get(next_tipo, 'Registrar')

    form_errors = {}
    form_values = {
        'id_funcionario': funcionario_id,
        'observacao': '',
    }

    if request.method == 'POST':
        form_values['observacao'] = (request.POST.get('observacao') or '').strip()

        if not funcionario:
            messages.error(request, 'Selecione um funcionário para registrar o ponto.')
        elif total_punches >= 4:
            messages.warning(request, 'Já existem 4 marcações (entrada/saída) registradas hoje para este funcionário.')
        else:
            payload = {
                'id_funcionario': funcionario.id_funcionario,
                'tipo': next_tipo,
                'observacao': form_values['observacao'],
            }
            serializer = RegistroPontoSerializer(data=payload)
            if serializer.is_valid():
                registro = serializer.save()
                messages.success(
                    request,
                    f'Ponto registrado: {registro.get_tipo_display()} — {timezone.localtime(registro.data_hora).strftime("%H:%M:%S")}'
                )
                return redirect(f'{reverse("ponto_registros")}?funcionario={funcionario.id_funcionario}')
            form_errors = serializer.errors

    def to_epoch_ms(dt):
        if not dt:
            return None
        return int(dt.timestamp() * 1000)

    tz_offset = server_now.utcoffset()
    clock_payload = {
        'server_epoch_ms': int(server_now.timestamp() * 1000),
        'server_tz_offset_min': int(tz_offset.total_seconds() / 60) if tz_offset else 0,
        'entrada1_epoch_ms': to_epoch_ms(entrada1.data_hora if entrada1 else None),
        'saida1_epoch_ms': to_epoch_ms(saida1.data_hora if saida1 else None),
        'entrada2_epoch_ms': to_epoch_ms(entrada2.data_hora if entrada2 else None),
        'saida2_epoch_ms': to_epoch_ms(saida2.data_hora if saida2 else None),
    }

    context = {
        'server_now': server_now,
        'clock_payload': clock_payload,
        'funcionarios': funcionarios,
        'funcionario': funcionario,
        'funcionario_id': funcionario_id,
        'slots': [
            {'label': 'Entrada', 'dt': entrada1.data_hora if entrada1 else None},
            {'label': 'Saída (intervalo)', 'dt': saida1.data_hora if saida1 else None},
            {'label': 'Entrada (retorno)', 'dt': entrada2.data_hora if entrada2 else None},
            {'label': 'Saída (fim)', 'dt': saida2.data_hora if saida2 else None},
        ],
        'total_trabalhado': format_hms(total_seconds),
        'total_punches': total_punches,
        'can_register': can_register,
        'next_label': next_label,
        'next_tipo': next_tipo,
        'form_errors': form_errors,
        'form_values': form_values,
    }
    return render(request, 'ponto/bate_ponto.html', context)


@login_required
def ponto_consultas_view(request):
    """Tela web para consumir endpoints do módulo de ponto (GET/DELETE/espelho) via JS."""
    funcionarios = Funcionario.objects.select_related('id_departamento', 'id_cargo').order_by('nome')
    context = {
        'funcionarios': funcionarios,
        'tipos': [
            ('', 'Todos'),
            ('entrada', 'Entrada'),
            ('saida', 'Saída'),
            ('pausa', 'Pausa'),
        ],
    }
    return render(request, 'ponto/registros.html', context)