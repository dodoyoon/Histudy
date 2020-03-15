# Generated by Django 2.1 on 2020-03-14 11:23

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0011_data_participator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='student_id',
            field=models.PositiveIntegerField(null=True, validators=[django.core.validators.MaxValueValidator(99999999)]),
        ),
    ]