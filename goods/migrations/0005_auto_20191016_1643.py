# Generated by Django 2.2.5 on 2019-10-16 16:43

from django.db import migrations, models
import goods.models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0004_auto_20191016_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='barang',
            name='slugifyBarang',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='barang',
            name='image1',
            field=models.ImageField(upload_to=goods.models.Barang.pathUpload),
        ),
        migrations.AlterField(
            model_name='barang',
            name='image2',
            field=models.ImageField(blank=True, null=True, upload_to=goods.models.Barang.pathUpload),
        ),
        migrations.AlterField(
            model_name='barang',
            name='image3',
            field=models.ImageField(blank=True, null=True, upload_to=goods.models.Barang.pathUpload),
        ),
        migrations.AlterField(
            model_name='barang',
            name='image4',
            field=models.ImageField(blank=True, null=True, upload_to=goods.models.Barang.pathUpload),
        ),
        migrations.AlterField(
            model_name='barang',
            name='image5',
            field=models.ImageField(blank=True, null=True, upload_to=goods.models.Barang.pathUpload),
        ),
    ]
