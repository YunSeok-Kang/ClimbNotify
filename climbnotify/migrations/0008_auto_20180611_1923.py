# Generated by Django 2.0.5 on 2018-06-11 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('climbnotify', '0007_auto_20180611_1915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mappositiondata',
            name='phase_three',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='mappositiondata',
            name='phase_two',
            field=models.CharField(max_length=32, null=True),
        ),
    ]