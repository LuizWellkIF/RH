from django.utils import timezone
from rest_framework import serializers
from .models import Funcionario


def validar_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise serializers.ValidationError('CPF inválido.')
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]):
            raise serializers.ValidationError('CPF inválido.')
    return cpf


class FuncionarioSerializer(serializers.ModelSerializer):
    cargo_nome = serializers.CharField(source='id_cargo.nome', read_only=True)
    departamento_nome = serializers.CharField(source='id_departamento.nome', read_only=True)
    tempo_empresa = serializers.SerializerMethodField()

    class Meta:
        model = Funcionario
        fields = [
            'id_funcionario',
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'salario',
            'status',
            'id_cargo',
            'cargo_nome',
            'id_departamento',
            'departamento_nome',
            'tempo_empresa',
        ]

    def validate_cpf(self, value):
        return validar_cpf(value)

    def get_tempo_empresa(self, obj):
        if not obj.data_admissao:
            return None
        admissao = obj.data_admissao
        if timezone.is_naive(admissao):
            admissao = timezone.make_aware(admissao, timezone.get_default_timezone())
        delta = timezone.now() - admissao
        anos = delta.days // 365
        meses = (delta.days % 365) // 30
        if anos > 0:
            return f'{anos} ano{"s" if anos > 1 else ""} e {meses} mês{"es" if meses > 1 else ""}'
        return f'{meses} mês{"es" if meses > 1 else ""}'