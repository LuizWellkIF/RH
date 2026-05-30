from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile
from funcionarios.models import Funcionario
from departamentos.models import Departamento


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={'placeholder': 'Seu usuário', 'autofocus': True})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )


class CriarUsuarioForm(forms.ModelForm):
    first_name  = forms.CharField(label='Nome')
    last_name   = forms.CharField(label='Sobrenome')
    password    = forms.CharField(label='Senha inicial', widget=forms.PasswordInput())
    setor = forms.ModelChoiceField(
        label='Setor / Departamento',
        queryset=Departamento.objects.all().order_by('nome'),
        empty_label='Selecione um departamento',
    )
    is_gerente  = forms.BooleanField(label='É gerente do setor?', required=False)
    funcionario = forms.ModelChoiceField(
        label='Funcionário vinculado',
        queryset=Funcionario.objects.filter(status='ativo', user_profile__isnull=True).order_by('nome'),
        required=False,
        empty_label='Selecione um funcionário (opcional)',
    )

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'is_gerente':
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                funcionario=self.cleaned_data.get('funcionario'),
                setor=self.cleaned_data['setor'],
                is_gerente=self.cleaned_data['is_gerente'],
            )
        return user


class AlterarSenhaForm(forms.Form):
    senha_atual    = forms.CharField(label='Senha atual',        widget=forms.PasswordInput())
    nova_senha     = forms.CharField(label='Nova senha',         widget=forms.PasswordInput())
    confirmar_senha = forms.CharField(label='Confirmar nova senha', widget=forms.PasswordInput())

    def clean(self):
        cleaned_data = super().clean()
        nova      = cleaned_data.get('nova_senha')
        confirmar = cleaned_data.get('confirmar_senha')
        if nova and confirmar and nova != confirmar:
            raise forms.ValidationError('As senhas não coincidem.')
        return cleaned_data
