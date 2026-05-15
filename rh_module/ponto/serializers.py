from rest_framework import serializers
from .models import RegistroPonto


class RegistroPontoSerializer(serializers.ModelSerializer):
    funcionario_nome = serializers.CharField(
        source='id_funcionario.nome',
        read_only=True
    )
    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )

    class Meta:
        model = RegistroPonto
        fields = [
            'id_registro',
            'id_funcionario',
            'funcionario_nome',
            'data_hora',
            'tipo',
            'tipo_display',
            'observacao',
        ]
        read_only_fields = ['data_hora']

    def validate(self, data):
        """Valida a sequência lógica dos registros do funcionário."""
        funcionario = data.get('id_funcionario')
        tipo = data.get('tipo')

        ultimo = (
            RegistroPonto.objects
            .filter(id_funcionario=funcionario)
            .order_by('-data_hora')
            .first()
        )

        if tipo == 'entrada' and ultimo and ultimo.tipo == 'entrada':
            raise serializers.ValidationError(
                'Já existe uma entrada registrada. Registre uma saída ou pausa primeiro.'
            )
        if tipo == 'saida' and (not ultimo or ultimo.tipo == 'saida'):
            raise serializers.ValidationError(
                'Não há entrada registrada para encerrar.'
            )
        if tipo == 'pausa' and (not ultimo or ultimo.tipo != 'entrada'):
            raise serializers.ValidationError(
                'Só é possível registrar pausa após uma entrada.'
            )
        return data