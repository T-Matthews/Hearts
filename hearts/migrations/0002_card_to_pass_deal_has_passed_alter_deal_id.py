# Generated by Django 4.1 on 2022-09-14 06:13

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('hearts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='to_pass',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='deal',
            name='has_passed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='deal',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
    ]
