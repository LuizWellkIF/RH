from django import forms
from django.core.exceptions import ValidationError

from .models import Funcionario


def _validar_cpf(value: str) -> str:
    cpf = ''.join(filter(str.isdigit, value or ''))

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')

    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]):
            raise ValidationError('CPF inválido.')

    return cpf


class FuncionarioForm(forms.ModelForm):
    data_admissao = forms.DateTimeField(
        label='Data de admissão',
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control', 'type': 'datetime-local'},
        ),
    )

    class Meta:
        model = Funcionario
        fields = [
            'nome',
            'cpf',
            'email',
            'telefone',
            'data_admissao',
            'salario',
            'status',
            'id_departamento',
            'id_cargo',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '11'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'salario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'id_departamento': forms.Select(attrs={'class': 'form-control'}),
            'id_cargo': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_cpf(self):
        return _validar_cpf(self.cleaned_data.get('cpf'))

    def clean(self):
        cleaned_data = super().clean()

        # Garante que o cargo pertença ao departamento selecionado (quando aplicável)
        departamento = cleaned_data.get('id_departamento')
        cargo = cleaned_data.get('id_cargo')
        if departamento and cargo and getattr(cargo, 'id_departamento_id', None) != departamento.id_departamento:
            self.add_error('id_cargo', 'O cargo selecionado não pertence ao departamento informado.')

        return cleaned_data
