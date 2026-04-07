from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_role):
    """
    Decorator que verifica se o usuário tem a role específica
    OU se ele é um superusuário (admin).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa fazer login para acessar esta página.')
                return redirect('login')
            
            if request.user.role == allowed_role or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'Acesso negado. Esta página é restrita.')
            return redirect('home')
            
        return _wrapped_view
    return decorator