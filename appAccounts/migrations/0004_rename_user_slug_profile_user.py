# Generated by Django 4.2.7 on 2025-04-22 03:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appAccounts', '0003_rename_user_profile_user_slug'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='user_slug',
            new_name='user',
        ),
    ]
