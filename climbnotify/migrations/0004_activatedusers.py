# Generated by Django 2.0.5 on 2018-06-08 10:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climbnotify', '0003_auto_20180608_1831'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivatedUsers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_logged_time', models.CharField(max_length=8)),
                ('updated_logged_time', models.CharField(max_length=8)),
                ('phase', models.IntegerField()),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climbnotify.User')),
            ],
        ),
    ]