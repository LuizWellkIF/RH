from rest_framework import serializers
from .models import Departamento

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = '__all__'
        
    def validate_sigla(self, value):
        '''
        Verifica se já existe um departamento com a mesma sigla, ignorando o caso e espaços em branco.
        '''
        value = value.upper().strip()
        
        qs = Departamento.objects.filter(sigla=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Já existe um departamento com essa sigla.')
        return value