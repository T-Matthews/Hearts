# Generated by Django 4.1 on 2022-09-16 05:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hearts', '0002_card_to_pass_deal_has_passed_alter_deal_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='bot_strategy',
            field=models.TextField(blank=True, null=True),
        ),
    ]