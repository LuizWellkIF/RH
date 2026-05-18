
from rest_framework import serializers
from .models import SolicitacaoFerias


class SolicitacaoFeriasSerializer(serializers.ModelSerializer):
    funcionario_nome = serializers.CharField(
        source='id_funcionario.nome',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    dias_solicitados = serializers.IntegerField(read_only=True)

    class Meta:
        model = SolicitacaoFerias
        fields = [
            'id_solicitacao',
            'id_funcionario',
            'funcionario_nome',
            'data_solicitacao',
            'data_inicio',
            'data_fim',
            'dias_solicitados',
            'status',
            'status_display',
            'observacao',
        ]
        read_only_fields = ['data_solicitacao', 'status']

    def validate(self, data):
        data_inicio = data.get('data_inicio')
        data_fim = data.get('data_fim')
        funcionario = data.get('id_funcionario')

        # Data fim deve ser posterior à data início
        if data_fim <= data_inicio:
            raise serializers.ValidationError(
                'A data de fim deve ser posterior à data de início.'
            )

        # Mínimo de 5 dias corridos
        if (data_fim - data_inicio).days + 1 < 5:
            raise serializers.ValidationError(
                'O período mínimo de férias é de 5 dias.'
            )

        # Verifica sobreposição com férias já aprovadas do mesmo funcionário
        sobreposicao = SolicitacaoFerias.objects.filter(
            id_funcionario=funcionario,
            status='aprovada',
            data_inicio__lte=data_fim,
            data_fim__gte=data_inicio,
        )
        # Ignora o próprio registro em caso de update
        if self.instance:
            sobreposicao = sobreposicao.exclude(pk=self.instance.pk)

        if sobreposicao.exists():
            raise serializers.ValidationError(
                'Já existe férias aprovadas nesse período para este funcionário.'
            )

        return data