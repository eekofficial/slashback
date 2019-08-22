# Generated by Django 2.1 on 2019-03-07 14:56

import cashback_app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cashback_app', '0060_auto_20190307_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='balance_rub',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10, verbose_name='Текущий баланс RUB'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='balance_usd',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10, verbose_name='Текущий баланс USD'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='post',
            name='photo',
            field=cashback_app.models.Photo(blank=True, null=True, upload_to=cashback_app.models.Photo.get_path, validators=[cashback_app.models.Photo.validate_image], verbose_name='Изображение, до 5МБ'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='photo',
            field=cashback_app.models.Photo(upload_to=cashback_app.models.Photo.get_path, validators=[cashback_app.models.Photo.validate_image], verbose_name='Фото программы'),
        ),
        migrations.AlterField(
            model_name='texts',
            name='start_photo_0',
            field=cashback_app.models.Photo(blank=True, null=True, upload_to=cashback_app.models.Photo.get_path, validators=[cashback_app.models.Photo.validate_image], verbose_name='Фото #1'),
        ),
        migrations.AlterField(
            model_name='texts',
            name='start_photo_1',
            field=cashback_app.models.Photo(blank=True, null=True, upload_to=cashback_app.models.Photo.get_path, validators=[cashback_app.models.Photo.validate_image], verbose_name='Фото #2'),
        ),
        migrations.AlterField(
            model_name='texts',
            name='start_photo_2',
            field=cashback_app.models.Photo(blank=True, null=True, upload_to=cashback_app.models.Photo.get_path, validators=[cashback_app.models.Photo.validate_image], verbose_name='Фото #3'),
        ),
        migrations.AlterField(
            model_name='texts',
            name='start_photo_3',
            field=cashback_app.models.Photo(blank=True, null=True, upload_to=cashback_app.models.Photo.get_path, validators=[cashback_app.models.Photo.validate_image], verbose_name='Фото #4'),
        ),
    ]