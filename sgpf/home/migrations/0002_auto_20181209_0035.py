# Generated by Django 2.1 on 2018-12-09 00:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='concept',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='concept',
            name='user',
        ),
        migrations.RemoveField(
            model_name='daily_input',
            name='concept',
        ),
        migrations.RemoveField(
            model_name='daily_input',
            name='user',
        ),
        migrations.DeleteModel(
            name='Concept',
        ),
        migrations.DeleteModel(
            name='Daily_Input',
        ),
    ]
