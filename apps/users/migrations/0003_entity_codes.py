from django.db import migrations, models


def populate_user_codes(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for i, obj in enumerate(User.objects.order_by('id'), start=1):
        obj.code = str(i)
        obj.save(update_fields=['code'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_branch_alter_user_role_usermoduleaccess'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='الكود'),
        ),
        migrations.RunPython(populate_user_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='code',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='الكود'),
        ),
    ]
