# Generated by Django 2.0.5 on 2018-06-11 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('climbnotify', '0005_auto_20180608_2238'),
    ]

    operations = [
        migrations.CreateModel(
            name='MapPositionData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phase_one', models.CharField(max_length=32)),
                ('phase_two', models.CharField(max_length=32)),
                ('phase_three', models.CharField(max_length=32)),
                ('posX', models.IntegerField()),
                ('posY', models.IntegerField()),
            ],
        ),
    ]
