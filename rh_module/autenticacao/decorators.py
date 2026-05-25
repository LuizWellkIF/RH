from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def rh_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.profile.is_rh:
            return render(request, 'autenticacao/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def gerente_required(view_func):
    """Restringe acesso a gerentes do setor de RH."""
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = request.user.profile
        if not profile.is_rh or not profile.is_gerente:
            return render(request, 'autenticacao/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper