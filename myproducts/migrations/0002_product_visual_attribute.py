# Generated by Django 5.2.1 on 2025-07-08 20:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myproducts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='visual_attribute',
            field=models.ForeignKey(blank=True, help_text='El atributo que controla las imágenes (ej. Color para ropa, Sabor para suplementos).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='visual_for_products', to='myproducts.attribute', verbose_name='Atributo Visual Principal'),
        ),
    ]
