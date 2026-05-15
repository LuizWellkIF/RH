from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import RegistroPonto
from .serializers import RegistroPontoSerializer


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