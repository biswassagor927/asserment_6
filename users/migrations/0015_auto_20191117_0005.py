# Generated by Django 2.2.6 on 2019-11-17 00:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_auto_20191110_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='alamat',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customuser',
            name='token',
            field=models.CharField(blank=True, max_length=37, null=True),
        ),
    ]
