from django.contrib import admin
from .models import PharmacyProfile, Branch, BarcodeLabelSettings

admin.site.register(PharmacyProfile)
admin.site.register(Branch)
admin.site.register(BarcodeLabelSettings)
