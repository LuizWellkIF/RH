from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone

from .forms import LoginForm, CriarUsuarioForm, AlterarSenhaForm
from .models import UserProfile
from .decorators import rh_required, gerente_required

from funcionarios.models import Funcionario
from departamentos.models import Departamento
from ponto.models import RegistroPonto
from ferias.models import SolicitacaoFerias


# ── Autenticação ──────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        if user.profile.primeiro_acesso:
            messages.warning(request, 'Bem-vindo! Por segurança, altere sua senha antes de continuar.')
            return redirect('alterar_senha')
        messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
        return redirect(request.GET.get('next', 'dashboard'))

    return render(request, 'autenticacao/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('login')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@rh_required
def dashboard_view(request):
    hoje = timezone.now()

    context = {
        'total_ativos':    Funcionario.objects.filter(status='ativo').count(),
        'total_afastados': Funcionario.objects.filter(status='afastado').count(),
        'total_inativos':  Funcionario.objects.filter(status='inativo').count(),
        'ultimos_funcionarios': Funcionario.objects.select_related(
            'id_cargo', 'id_departamento'
        ).order_by('-id_funcionario')[:5],
        'total_departamentos': Departamento.objects.count(),
        'registros_hoje': RegistroPonto.objects.filter(
            data_hora__date=hoje.date()
        ).count(),
        'total_ferias_pendentes': SolicitacaoFerias.objects.filter(status='pendente').count(),
        'ferias_pendentes': SolicitacaoFerias.objects.filter(
            status='pendente'
        ).select_related('id_funcionario').order_by('data_inicio')[:3],
    }

    return render(request, 'autenticacao/dashboard.html', context)


# ── Usuários do sistema ───────────────────────────────────────────────────────

@gerente_required
def listar_usuarios_view(request):
    usuarios = UserProfile.objects.select_related('user', 'funcionario').all()
    return render(request, 'autenticacao/listar_usuarios.html', {'usuarios': usuarios})


@gerente_required
def criar_usuario_view(request):
    form = CriarUsuarioForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        senha = form.cleaned_data['password']
        return render(request, 'autenticacao/criar_usuario.html', {
            'form': CriarUsuarioForm(),
            'usuario_criado': user,
            'senha_gerada': senha,
        })

    return render(request, 'autenticacao/criar_usuario.html', {'form': form})


@gerente_required
def editar_usuario_view(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)

    if request.method == 'POST':
        user = profile.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name',  user.last_name)
        user.email      = request.POST.get('email',      user.email)
        user.save()

        profile.setor      = request.POST.get('setor',      profile.setor)
        profile.is_gerente = request.POST.get('is_gerente') == 'on'
        profile.save()

        messages.success(request, 'Usuário atualizado com sucesso!')
        return redirect('listar_usuarios')

    return render(request, 'autenticacao/editar_usuario.html', {'profile': profile})


@gerente_required
def desativar_usuario_view(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)

    if profile.user == request.user:
        messages.error(request, 'Você não pode desativar seu próprio usuário.')
        return redirect('listar_usuarios')

    if request.method == 'POST':
        profile.user.is_active = False
        profile.user.save()
        messages.success(request, f'Usuário {profile.user.username} desativado.')
        return redirect('listar_usuarios')

    return render(request, 'autenticacao/confirmar_desativar.html', {'profile': profile})


@gerente_required
def reativar_usuario_view(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)

    if request.method == 'POST':
        profile.user.is_active = True
        profile.user.save()
        messages.success(request, f'Usuário {profile.user.username} reativado.')
        return redirect('listar_usuarios')

    return render(request, 'autenticacao/confirmar_reativar.html', {'profile': profile})


@gerente_required
def redefinir_senha_view(request, pk):
    """Gerente redefine a senha de um usuário, forçando troca no próximo acesso."""
    profile = get_object_or_404(UserProfile, pk=pk)

    if request.method == 'POST':
        nome_parts  = profile.user.first_name.lower().split()
        primeiro    = nome_parts[0] if nome_parts else profile.user.username
        ultimo      = profile.user.last_name.lower().split()[-1] if profile.user.last_name else primeiro
        nova_senha  = f'{primeiro}.{ultimo}123'

        profile.user.set_password(nova_senha)
        profile.user.save()
        profile.primeiro_acesso = True
        profile.save()

        messages.success(
            request,
            f'Senha de {profile.user.get_full_name()} redefinida para: {nova_senha}'
        )
        return redirect('listar_usuarios')

    return render(request, 'autenticacao/confirmar_redefinir_senha.html', {'profile': profile})


# ── Senha ─────────────────────────────────────────────────────────────────────

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
            login(request, user)
            user.profile.primeiro_acesso = False
            user.profile.save()
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('dashboard')

    return render(request, 'autenticacao/alterar_senha.html', {'form': form})