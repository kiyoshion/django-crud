# Generated by Django 3.2.4 on 2021-06-04 23:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('item', '0003_auto_20210605_0836'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemmodel',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='item/'),
        ),
    ]
