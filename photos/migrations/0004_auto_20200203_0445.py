# Generated by Django 3.0.1 on 2020-02-03 04:45

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0003_auto_20200202_0808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]