# Generated by Django 4.2.7 on 2025-04-03 08:42

from django.db import migrations
from django.utils.text import slugify


def populate_machine_name(apps, schema_editor):
    # Get the historical version of the model
    KnowledgeResources = apps.get_model("appAdmin", "KnowledgeResources")

    # Loop through all existing records
    resources = []
    for resource in KnowledgeResources.objects.all():
        # Generate the machine_name
        resource.machine_name = slugify(resource.knowledge_title).replace("-", "_")
        resources.append(resource)

    # Bulk update all records for better performance
    if resources:
        KnowledgeResources.objects.bulk_update(resources, ["machine_name"])


def reverse_populate_machine_name(apps, schema_editor):
    # Get the historical version of the model
    KnowledgeResources = apps.get_model("appAdmin", "KnowledgeResources")

    # Clear all machine_name values
    KnowledgeResources.objects.update(machine_name="")


class Migration(migrations.Migration):

    dependencies = [
        ("appAdmin", "0002_knowledgeresources_machine_name"),
    ]

    operations = [
        migrations.RunPython(populate_machine_name, reverse_populate_machine_name),
    ]
