from django.db import migrations, models


def populate_expense_category_codes(apps, schema_editor):
    ExpenseCategory = apps.get_model('treasury', 'ExpenseCategory')
    for i, obj in enumerate(ExpenseCategory.objects.order_by('id'), start=1):
        obj.code = str(i)
        obj.save(update_fields=['code'])


class Migration(migrations.Migration):

    dependencies = [
        ('treasury', '0004_cashbox_bank_balance'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expensecategory',
            options={'ordering': ['code'], 'verbose_name': 'بند مصروف', 'verbose_name_plural': 'بنود المصروفات'},
        ),
        migrations.AddField(
            model_name='expensecategory',
            name='code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='الكود'),
        ),
        migrations.RunPython(populate_expense_category_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='expensecategory',
            name='code',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='الكود'),
        ),
    ]
