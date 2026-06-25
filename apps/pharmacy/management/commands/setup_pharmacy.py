from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.pharmacy.models import PharmacyProfile
from apps.users.models import UserModuleAccess


class Command(BaseCommand):
    help = 'إعداد النظام الأولي — مدير نظام فقط (بدون أصناف أو بيانات تجريبية)'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--pharmacy-name', default='')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password']

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username, password=password, role=User.Role.ADMIN,
            )
            for module, _ in UserModuleAccess.Module.choices:
                UserModuleAccess.objects.create(
                    user=user, module=module,
                    can_view=True, can_add=True, can_edit=True, can_delete=True,
                )
            self.stdout.write(self.style.SUCCESS(f'User created: {username}'))
        else:
            self.stdout.write(f'User exists: {username}')

        if not PharmacyProfile.objects.exists():
            name = options['pharmacy_name'] or 'صيدليتي'
            PharmacyProfile.objects.create(name=name)
            self.stdout.write(self.style.SUCCESS(f'Pharmacy profile: {name}'))

        self.stdout.write(self.style.SUCCESS('Setup complete — no sample inventory data added.'))
        self.stdout.write('Run: python manage.py runserver')
