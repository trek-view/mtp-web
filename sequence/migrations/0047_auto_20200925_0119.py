# Generated by Django 3.0.3 on 2020-09-25 00:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sequence', '0046_imagelabel_unique_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='labeltype',
            name='type',
            field=models.CharField(choices=[('polygon', 'polygon')], default='polygon', max_length=50),
        ),
    ]