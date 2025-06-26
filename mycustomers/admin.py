from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import CustomerProfile

# Desregistrar el UserAdmin base si vas a usar uno personalizado
# admin.site.unregister(User)

class CustomerProfileInline(admin.StackedInline): # O admin.TabularInline para un look más compacto
    model = CustomerProfile
    can_delete = False # No permitir borrar el perfil desde el User admin, se borra con el User
    verbose_name_plural = 'Perfil de Cliente'
    fk_name = 'user'
    fields = ('DNI', 'telefono', 'direccion') # Campos a mostrar en el inline

# Define un nuevo User admin
class UserAdmin(BaseUserAdmin):
    inlines = (CustomerProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_dni', 'get_telefono')
    list_select_related = ('customerprofile',) # Optimización para obtener el perfil

    def get_dni(self, instance):
        try:
            return instance.customerprofile.DNI
        except CustomerProfile.DoesNotExist:
            return "N/A"
    get_dni.short_description = 'DNI'

    def get_telefono(self, instance):
        try:
            return instance.customerprofile.telefono
        except CustomerProfile.DoesNotExist:
            return "N/A"
    get_telefono.short_description = 'Teléfono'

    # Puedes añadir más campos del perfil a search_fields si es necesario
    # search_fields = BaseUserAdmin.search_fields + ('customerprofile__DNI', 'customerprofile__telefono')


# Re-registrar UserAdmin (o registrar si desregistraste el base)
admin.site.unregister(User) # Necesario si vas a sobreescribir el UserAdmin
admin.site.register(User, UserAdmin)

# También puedes registrar CustomerProfile por separado si quieres gestionarlo directamente
# (aunque es más intuitivo a través del User)
@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nombre_completo', 'correo_electronico', 'DNI', 'telefono', 'actualizado')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'DNI', 'telefono')
    list_filter = ('user__is_active', 'actualizado')
    readonly_fields = ('user', 'creado', 'actualizado') # User no se debería cambiar desde aquí
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Información de Contacto', {'fields': ('DNI', 'telefono')}),
        ('Dirección', {'fields': ('direccion',)}),
        ('Timestamps', {'fields': ('creado', 'actualizado')}),
    )

    def nombre_completo(self, obj):
        return obj.user.get_full_name()
    nombre_completo.short_description = "Nombre Completo"

    def correo_electronico(self, obj):
        return obj.user.email
    correo_electronico.short_description = "Correo Electrónico"