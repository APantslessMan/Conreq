# Generated by Django 3.1.5 on 2021-02-03 07:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportedIssue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('resolution', models.CharField(max_length=255)),
                ('date_reported', models.DateTimeField(auto_now_add=True)),
                ('content_id', models.CharField(max_length=30)),
                ('source', models.CharField(max_length=30)),
                ('content_type', models.CharField(max_length=30)),
                ('seasons', models.TextField(blank=True)),
                ('episode_ids', models.TextField(blank=True)),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
