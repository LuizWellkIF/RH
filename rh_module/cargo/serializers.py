from rest_framework import serializers
from .models import Cargo


class CargoSerializer(serializers.ModelSerializer):
    departamento_nome = serializers.CharField(
        source='id_departamento.nome',
        read_only=True
    )
    nivel_display = serializers.CharField(
        source='get_nivel_display',
        read_only=True
    )

    class Meta:
        model = Cargo
        fields = [
            'id_cargo',
            'id_departamento',
            'departamento_nome',
            'nome',
            'descricao',
            'nivel',
            'nivel_display',
        ]