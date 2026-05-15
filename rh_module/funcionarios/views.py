from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .models import Funcionario
from .serializers import FuncionarioSerializer


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