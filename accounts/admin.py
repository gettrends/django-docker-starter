from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User, Role


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'role', 'is_active', 'is_verified', 'is_superuser')


class UserAdmin(admin.ModelAdmin):
    form = UserChangeForm

    list_display = ('email', 'role', 'is_verified')
    list_filter = ('role',)
    fieldsets = (
        (None, {'fields': ('email', 'is_active', 'is_verified', 'is_superuser',)}),
        ('Permissions', {'fields': ('role',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'is_verified')}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class RoleAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Role, RoleAdmin)

admin.site.unregister(Group)
