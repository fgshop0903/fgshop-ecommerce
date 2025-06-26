from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView # CreateView podría no ser necesario si UserRegisterView se va
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView # Si mantienes CustomLoginView/LogoutView aquí
from django.contrib.auth.models import User
from django.contrib.auth import login # Si lo usabas en UserRegisterView
from django.contrib import messages
from .models import CustomerProfile
# ACTUALIZA ESTA LÍNEA:
from .forms import CustomerProfileForm, UserUpdateForm # Ya no importamos CustomUserCreationForm
# Si creaste CustomLoginFormAllauth y CustomSignupFormAllauth y los usas en settings.py para allauth,
# no necesitas importarlos aquí A MENOS QUE tengas vistas en este archivo que los usen directamente.


class StaffRequiredMixin(UserPassesTestMixin):
    """Solo permite acceso a staff users."""
    def test_func(self):
        return self.request.user.is_staff

class CustomerProfileDetailView(LoginRequiredMixin, DetailView):
    model = CustomerProfile
    template_name = 'mycustomers/customer_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        # Si el usuario no es staff, solo puede ver su propio perfil
        # Si es staff, puede ver perfiles por username en la URL
        username = self.kwargs.get('username')
        if username and self.request.user.is_staff:
            user = get_object_or_404(User, username=username)
            return get_object_or_404(CustomerProfile, user=user)
        return get_object_or_404(CustomerProfile, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Perfil de {self.object.user.get_full_name() or self.object.user.username}"
        # Se puede comprobar si el perfil que se ve es el del usuario logueado
        context['is_own_profile'] = (self.object.user == self.request.user)
        return context


class CustomerProfileUpdateView(LoginRequiredMixin, FormView):
    template_name = 'mycustomers/customer_profile_form.html'
    form_class = CustomerProfileForm # Solo para el perfil
    second_form_class = UserUpdateForm # Para el User
    success_url = reverse_lazy('mycustomers:profile_detail_self') # Redirigir al perfil

    def get_object(self): # Helper para obtener el perfil del usuario logueado
        return get_object_or_404(CustomerProfile, user=self.request.user)

    def get_initial(self):
        """Devuelve los datos iniciales para los formularios."""
        initial = super().get_initial()
        profile = self.get_object()
        user = self.request.user
        initial['DNI'] = profile.DNI
        initial['telefono'] = profile.telefono
        initial['direccion'] = profile.direccion
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        initial['email'] = user.email
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = self.form_class(instance=self.get_object(), initial=self.get_initial())
        if 'form2' not in context:
            context['form2'] = self.second_form_class(instance=self.request.user, initial=self.get_initial())
        context['titulo_pagina'] = "Editar Mi Perfil"
        return context

    def post(self, request, *args, **kwargs):
        """Maneja el POST para ambos formularios."""
        profile = self.get_object()
        user = request.user
        form = self.form_class(request.POST, instance=profile)
        form2 = self.second_form_class(request.POST, instance=user)

        if form.is_valid() and form2.is_valid():
            form.save()
            form2.save()
            messages.success(request, "Tu perfil ha sido actualizado exitosamente.")
            return redirect(self.get_success_url())
        else:
            # Si hay errores, volver a renderizar con los formularios y sus errores
            return self.render_to_response(self.get_context_data(form=form, form2=form2))


# Vistas para administración (solo staff)
class CustomerListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = CustomerProfile # O User, dependiendo de qué quieras listar
    template_name = 'mycustomers/customer_list.html'
    context_object_name = 'profiles' # o 'users'
    paginate_by = 20

    def get_queryset(self):
        # Puedes añadir filtros aquí, ej. buscar por nombre
        return CustomerProfile.objects.select_related('user').all().order_by('user__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Lista de Clientes"
        return context