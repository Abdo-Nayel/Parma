from django.conf import settings
from django.core.cache import cache


def pharmacy_info(request):
    profile = cache.get('pharmacy_profile')
    if profile is None:
        from .models import PharmacyProfile
        profile = PharmacyProfile.objects.first()
        cache.set('pharmacy_profile', profile, 300)
    return {
        'pharmacy': profile,
        'static_version': settings.STATIC_VERSION,
    }
