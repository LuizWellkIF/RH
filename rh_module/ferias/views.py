from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import SolicitacaoFerias
from .serializers import SolicitacaoFeriasSerializer


class SolicitacaoFeriasViewSet(viewsets.ModelViewSet):
    queryset = SolicitacaoFerias.objects.select_related('id_funcionario').all()
    serializer_class = SolicitacaoFeriasSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['id_funcionario', 'status']
    ordering_fields = ['data_solicitacao', 'data_inicio']

    @action(detail=True, methods=['patch'], url_path='aprovar')
    def aprovar(self, request, pk=None):
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