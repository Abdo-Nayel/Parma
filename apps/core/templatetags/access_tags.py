from django import template

from apps.core.permissions import user_can

register = template.Library()


@register.simple_tag(takes_context=True)
def can_access(context, module, action='view'):
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return user_can(request.user, module, action)
