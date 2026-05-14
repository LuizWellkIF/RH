from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile


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
    """Formulário para Gerente cadastrar novo usuário do sistema."""
    first_name = forms.CharField(label='Nome')
    last_name = forms.CharField(label='Sobrenome')
    password = forms.CharField(
        label='Senha inicial',
        widget=forms.PasswordInput()
    )
    cargo_rh = forms.ChoiceField(
        label='Cargo no RH',
        choices=UserProfile.CARGO_RH_CHOICES
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                cargo_rh=self.cleaned_data['cargo_rh']
            )
        return user


class AlterarSenhaForm(forms.Form):
    senha_atual = forms.CharField(label='Senha atual', widget=forms.PasswordInput())
    nova_senha = forms.CharField(label='Nova senha', widget=forms.PasswordInput())
    confirmar_senha = forms.CharField(label='Confirmar nova senha', widget=forms.PasswordInput())

    def clean(self):
        cleaned_data = super().clean()
        nova = cleaned_data.get('nova_senha')
        confirmar = cleaned_data.get('confirmar_senha')
        if nova and confirmar and nova != confirmar:
            raise forms.ValidationError('As senhas não coincidem.')
        return cleaned_data