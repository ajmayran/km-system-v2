# Generated by Django 4.2.7 on 2025-07-05 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appCmi', '0005_faqview'),
    ]

    operations = [
        migrations.AddField(
            model_name='faq',
            name='anonymous_reactions',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
