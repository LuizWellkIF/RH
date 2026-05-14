from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, CriarUsuarioForm, AlterarSenhaForm
from .models import UserProfile

# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
        return redirect(request.GET.get('next', 'dashboard'))

    return render(request, 'autenticacao/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('login')


@login_required
def dashboard_view(request):
    context = {
        # Esses valores serão preenchidos conforme os outros apps forem criados
        'total_ativos': 0,
        'total_departamentos': 0,
        'total_ferias_pendentes': 0,
        'registros_hoje': 0,
        'ultimos_funcionarios': [],
        'ferias_pendentes': [],
    }
    return render(request, 'autenticacao/dashboard.html', context)


@login_required
def criar_usuario_view(request):
    # Apenas gerentes podem cadastrar novos usuários
    if not request.user.profile.is_gerente:
        messages.error(request, 'Acesso negado. Apenas gerentes podem cadastrar usuários.')
        return redirect('dashboard')

    form = CriarUsuarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuário criado com sucesso!')
        return redirect('listar_usuarios')

    return render(request, 'autenticacao/criar_usuario.html', {'form': form})


@login_required
def listar_usuarios_view(request):
    if not request.user.profile.is_gerente:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    usuarios = UserProfile.objects.select_related('user', 'funcionario').all()
    return render(request, 'autenticacao/listar_usuarios.html', {'usuarios': usuarios})


@login_required
def alterar_senha_view(request):
    form = AlterarSenhaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = request.user
        if not user.check_password(form.cleaned_data['senha_atual']):
            messages.error(request, 'Senha atual incorreta.')
        else:
            user.set_password(form.cleaned_data['nova_senha'])
            user.save()
            login(request, user)  # mantém a sessão após troca de senha
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('dashboard')

    return render(request, 'autenticacao/alterar_senha.html', {'form': form})