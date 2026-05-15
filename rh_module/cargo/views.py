from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cargo
from .serializers import CargoSerializer


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.select_related('id_departamento').all()
    serializer_class = CargoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id_departamento', 'nivel']
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'nivel'] 