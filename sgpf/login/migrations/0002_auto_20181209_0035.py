# Generated by Django 2.1 on 2018-12-09 00:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='savings',
            name='user',
        ),
        migrations.RemoveField(
            model_name='savings_percentage',
            name='user',
        ),
        migrations.DeleteModel(
            name='Savings',
        ),
        migrations.DeleteModel(
            name='Savings_Percentage',
        ),
    ]
