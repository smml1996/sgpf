# Generated by Django 2.1 on 2018-10-25 03:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_auto_20181023_0642'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='concept',
            unique_together={('name', 'id')},
        ),
    ]
