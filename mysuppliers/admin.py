import pandas as pd
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import path, reverse 
from django.contrib import admin
from django.utils.html import format_html
from .models import Supplier
from .forms import SupplierImportForm
from django.contrib import messages


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_empresa', 'ruc', 'logo_thumbnail', 'nombre_contacto', 'telefono_contacto',
        'tipo_proveedor', 'estado', 'calificacion_interna'
    )
    list_filter = ('estado', 'tipo_proveedor', 'calificacion_interna', 'fecha_registro')
    search_fields = (
        'nombre_empresa', 'ruc', 'nombre_contacto',
        'correo_contacto', 'sitio_web'
    )
    fieldsets = (
        ("Información Principal", {
            'fields': ('nombre_empresa', 'ruc', 'estado', 'tipo_proveedor')
        }),
        ("Información de Contacto", {
            'fields': ('nombre_contacto', 'telefono_contacto', 'correo_contacto', 'sitio_web', 'logo')
        }),
        ("Direcciones", {
            'fields': ('direccion_fiscal', 'direccion_almacen')
        }),
        ("Condiciones y Evaluación", {
            'fields': ('terminos_pago', 'tiempo_entrega_promedio_a_fg', 'calificacion_interna')
        }),
        ("Notas Adicionales", {
            'fields': ('observaciones_generales',)
        }),
        ("Auditoría", {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',), 
        }),
    )
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')

    def logo_thumbnail(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width: 60px; height: auto;" />', obj.logo.url)
        return "-"
    logo_thumbnail.short_description = 'Logo'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-suppliers/',
                self.admin_site.admin_view(self.import_suppliers_view),
                name='supplier_import',
            )
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_url'] = reverse('admin:supplier_import')
        return super().changelist_view(request, extra_context=extra_context)

    def import_suppliers_view(self, request):
        if request.method == 'POST':
            form = SupplierImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                try:
                    df = pd.read_excel(file, dtype=str).fillna('') # Lee todo como texto y rellena vacíos
                    self.process_supplier_excel(request, df)
                    return redirect(reverse('admin:mysuppliers_supplier_changelist'))
                except Exception as e:
                    messages.error(request, f"Error al procesar el archivo: {e}")
        else:
            form = SupplierImportForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Importar Proveedores desde Excel',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/import_form.html', context)

    def process_supplier_excel(self, request, df):
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    ruc = str(row['ruc']).strip()
                    if not ruc: # Si el RUC está vacío, saltamos la fila
                        continue

                    supplier, created = Supplier.objects.update_or_create(
                        ruc=ruc,
                        defaults={
                            'nombre_empresa': str(row['nombre_empresa']).strip(),
                            'nombre_contacto': row.get('nombre_contacto', ''),
                            'telefono_contacto': row.get('telefono_contacto', ''),
                            'correo_contacto': row.get('correo_contacto', ''),
                            'sitio_web': row.get('sitio_web', ''),
                            'direccion_fiscal': row.get('direccion_fiscal', ''),
                            'direccion_almacen': row.get('direccion_almacen', ''),
                            'estado': 'Activo'
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    error_message = f"Error en la fila {index + 2} del Excel: {e}"
                    messages.error(request, error_message)
                    raise transaction.TransactionManagementError("Fallo en la importación para revertir cambios.")

        success_message = f"Importación exitosa: {created_count} proveedores creados, {updated_count} actualizados."
        messages.success(request, success_message)