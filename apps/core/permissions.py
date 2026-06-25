from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from apps.users.models import User, UserModuleAccess

MODULE_CHOICES = UserModuleAccess.Module.choices


def user_can(user, module, action='view'):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.role == User.Role.ADMIN:
        return True

    access_qs = user.module_access.all()
    if not access_qs.exists():
        return action == 'view'

    try:
        access = access_qs.get(module=module)
    except UserModuleAccess.DoesNotExist:
        return False
    return getattr(access, f'can_{action}', False)


def require_module(module, action='view'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not user_can(request.user, module, action):
                messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الشاشة.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
