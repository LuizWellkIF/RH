from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Departamento
from .serializers import DepartamentoSerializer
# Create your views here.

'''
ViewSet para o modelo Departamento, utilizando o ModelViewSet do Django REST Framework para fornecer as operações CRUD automaticamente.
'''
class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'sigla']
    ordering_fields = ['nome', 'sigla']

    @action(detail=True, methods=['get'], url_path='funcionarios')
    def listar_funcionarios(self, request, pk=None):
        """
        Retorna todos os funcionários do departamento.
        """
        departamento = self.get_object()
        
        from funcionarios.models import Funcionario
        
        from funcionarios.serializers import FuncionarioSerializer
        
        funcionarios = Funcionario.objects.filter(id_departamento=departamento)
        serializer = FuncionarioSerializer(funcionarios, many=True)
        
        return Response(serializer.data)