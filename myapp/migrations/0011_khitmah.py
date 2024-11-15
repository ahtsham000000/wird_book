# Generated by Django 5.1 on 2024-11-14 21:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_alter_communitymember_community'),
    ]

    operations = [
        migrations.CreateModel(
            name='Khitmah',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numberofkhitmah', models.PositiveIntegerField()),
                ('enddate', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.phonenumber')),
            ],
        ),
    ]
