from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # Para permisos
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import Supplier
from .forms import SupplierForm

# Asumimos que solo el personal (staff) puede gestionar proveedores
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class SupplierListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Supplier
    template_name = 'mysuppliers/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 15 # O el número que prefieras

    def get_queryset(self):
        # Puedes añadir filtros aquí, ej. por estado o búsqueda
        query = self.request.GET.get('q')
        qs = Supplier.objects.all().order_by('nombre_empresa')
        if query:
            qs = qs.filter(models.Q(nombre_empresa__icontains=query) | models.Q(ruc__icontains=query))
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Listado de Proveedores"
        context['search_query'] = self.request.GET.get('q', '')
        return context

class SupplierDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Supplier
    template_name = 'mysuppliers/supplier_detail.html'
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Detalle de Proveedor: {self.object.nombre_empresa}"
        # Aquí podrías añadir lógica para mostrar productos asociados de este proveedor si tuvieras el modelo SupplierProduct
        # context['productos_proveedor'] = self.object.supplierproduct_set.all()
        return context

class SupplierCreateView(LoginRequiredMixin, StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'mysuppliers/supplier_form.html'
    success_url = reverse_lazy('mysuppliers:supplier_list')
    success_message = "Proveedor '%(nombre_empresa)s' creado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nuevo Proveedor"
        context['nombre_boton'] = "Guardar Proveedor"
        return context

class SupplierUpdateView(LoginRequiredMixin, StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'mysuppliers/supplier_form.html'
    success_message = "Proveedor '%(nombre_empresa)s' actualizado exitosamente."
    # success_url se puede omitir si se usa get_absolute_url en el modelo
    
    def get_success_url(self):
        return reverse_lazy('mysuppliers:supplier_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Editar Proveedor: {self.object.nombre_empresa}"
        context['nombre_boton'] = "Actualizar Proveedor"
        return context

class SupplierDeleteView(LoginRequiredMixin, StaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Supplier
    template_name = 'mysuppliers/supplier_confirm_delete.html' # Crear esta plantilla
    success_url = reverse_lazy('mysuppliers:supplier_list')
    success_message = "Proveedor eliminado exitosamente."

    # Para que SuccessMessageMixin funcione con DeleteView
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Proveedor '{obj.nombre_empresa}' eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Confirmar Eliminación: {self.object.nombre_empresa}"
        return context