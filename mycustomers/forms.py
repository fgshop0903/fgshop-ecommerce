# mycustomers/forms.py

from django import forms
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm, LoginForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from .models import CustomerProfile
from django.utils.text import slugify
import random

# ==========================================================
# FORMULARIO DE REGISTRO CON USERNAME Y SUGERENCIAS
# ==========================================================
class CustomSignupFormAllauth(SignupForm):
    # 1. Definimos todos los campos que queremos en el formulario
    nombres = forms.CharField(max_length=30, label='Nombres', required=True,
                                widget=forms.TextInput(attrs={'placeholder': 'Escribe tus nombres'}))
    apellidos = forms.CharField(max_length=30, label='Apellidos', required=True,
                                  widget=forms.TextInput(attrs={'placeholder': 'Escribe tus apellidos'}))
    
    # ¡Añadimos el campo username!
    username = forms.CharField(max_length=150, label='Nombre de Usuario', required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'Elige un nombre de usuario único'}))
    
    title_preference = forms.ChoiceField(
        choices=CustomerProfile.TitleChoices.choices,
        widget=forms.RadioSelect, # Para que se vean como botones de opción
        label="Para darte un trato especial, ¿cómo te llamamos?",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(CustomSignupFormAllauth, self).__init__(*args, **kwargs)
        # Aquí ya no necesitamos hacer pop('username') porque lo hemos definido nosotros.
        
        # Personalizamos los campos que hereda de allauth
        if 'email' in self.fields: 
            self.fields['email'].label = "Correo Electrónico" 
            self.fields['email'].widget.attrs.update({'placeholder': 'tu.correo@ejemplo.com'})
        if 'password' in self.fields:
            self.fields['password'].label = "Contraseña"


    # 2. MÉTODO DE VALIDACIÓN INTELIGENTE PARA EL USERNAME
    def clean_username(self):
        username = self.cleaned_data['username']
        
        # Comprobar si el username ya existe (ignorando mayúsculas/minúsculas)
        if User.objects.filter(username__iexact=username).exists():
            suggestions = []
            
            # Obtener nombres y apellidos para generar sugerencias
            nombres = self.cleaned_data.get('nombres', '').lower()
            apellidos = self.cleaned_data.get('apellidos', '').lower()

            if nombres and apellidos:
                # Sugerencia 1: nombre.apellido
                sug1 = slugify(f"{nombres.split()[0]}.{apellidos.split()[0]}")
                if not User.objects.filter(username__iexact=sug1).exists():
                    suggestions.append(sug1)

                # Sugerencia 2: inicial_nombre + apellido
                sug2 = slugify(f"{nombres[0]}{apellidos.replace(' ', '')}")
                if not User.objects.filter(username__iexact=sug2).exists() and sug2 not in suggestions:
                    suggestions.append(sug2)

            # Sugerencia 3: username + número aleatorio
            sug3 = f"{username}{random.randint(10, 99)}"
            while User.objects.filter(username__iexact=sug3).exists():
                sug3 = f"{username}{random.randint(10, 99)}"
            if sug3 not in suggestions:
                suggestions.append(sug3)

            # Lanzar el error de validación con las sugerencias adjuntas
            raise forms.ValidationError(
                "Este nombre de usuario ya está en uso. ¿Qué tal alguna de estas opciones?",
                code='username_taken', # Un código de error por si lo necesitas
                params={'suggestions': suggestions[:3]} # Mostramos hasta 3 sugerencias
            )
            
        return username


    # 3. Guardar los datos extra en el modelo User
    def save(self, request):
        # Primero, dejamos que el SignupForm de allauth cree el usuario
        user = super(CustomSignupFormAllauth, self).save(request)
        
        # Ahora, añadimos nuestros datos personalizados
        user.first_name = self.cleaned_data['nombres']
        user.last_name = self.cleaned_data['apellidos']
        user.save() # Guardamos los cambios en el usuario
        
        try:
            profile = user.customerprofile
            profile.title_preference = self.cleaned_data['title_preference']
            profile.save()
        except CustomerProfile.DoesNotExist:
            # Plan B: si el signal fallara, creamos el perfil aquí
            CustomerProfile.objects.create(
                user=user, 
                title_preference=self.cleaned_data['title_preference']
            )

        return user


# ==========================================================
# FORMULARIO DE LOGIN (SIN CAMBIOS, PERO LIMPIADO)
# ==========================================================
class CustomLoginFormAllauth(LoginForm):
    def __init__(self, *args, **kwargs):
        super(CustomLoginFormAllauth, self).__init__(*args, **kwargs)
        
        if 'login' in self.fields:
            self.fields['login'].widget.attrs.update({'placeholder': 'Nombre de usuario o correo'})
            self.fields['login'].label = "Nombre de Usuario o Correo"
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({'placeholder': 'Contraseña'})
            self.fields['password'].label = "Contraseña"
        if 'remember' in self.fields:
             self.fields['remember'].label = "Recordarme en este equipo"

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout('login', 'password')

# ==========================================================
# FORMULARIOS DE PERFIL (SIN CAMBIOS)
# ==========================================================
class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['DNI', 'telefono', 'direccion']
        

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']