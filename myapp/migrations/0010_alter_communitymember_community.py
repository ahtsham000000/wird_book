# Generated by Django 5.1 on 2024-11-14 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_communitymember_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communitymember',
            name='community',
            field=models.IntegerField(choices=[(1, 'shared dhikr'), (2, 'Noticeboard'), (3, 'Question/Answer'), (4, 'Donate')]),
        ),
    ]
