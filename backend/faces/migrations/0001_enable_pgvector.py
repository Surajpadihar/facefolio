from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    """Enable the pgvector extension before any vector column/index is created."""

    initial = True

    dependencies = []

    operations = [
        VectorExtension(),
    ]
