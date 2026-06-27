from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_entity_codes'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='dashboard_shortcuts',
            field=models.JSONField(blank=True, default=list, verbose_name='اختصارات لوحة التحكم'),
        ),
    ]
