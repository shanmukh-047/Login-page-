from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import AccountProfile

User = get_user_model()

# Fields only a superuser may change: these are what make an account an administrator.
PRIVILEGE_FIELDS = ("is_staff", "is_superuser", "groups", "user_permissions")


class AccountProfileInline(admin.StackedInline):
    model = AccountProfile
    can_delete = False
    extra = 1
    max_num = 1


class ProtoLearnUserAdmin(UserAdmin):
    """Django's own user admin, with guard rails for non-superuser account managers.

    Built-in behaviour reused as-is: unique usernames, hashed passwords (set and reset
    via Django's password forms), and the 'Active' checkbox to enable or disable login.
    """

    inlines = [AccountProfileInline]
    list_display = ("username", "first_name", "last_name", "email", "is_active", "is_staff", "last_login")
    list_filter = ("is_active", "is_staff")

    def _is_manager_only(self, request):
        return not request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self._is_manager_only(request):
            # Account managers only see and edit student/customer accounts.
            qs = qs.filter(is_staff=False, is_superuser=False)
        return qs

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj is not None and self._is_manager_only(request):
            ro += [f for f in PRIVILEGE_FIELDS if f not in ro]
        return ro

    def has_change_permission(self, request, obj=None):
        if obj is not None and self._is_manager_only(request) and (obj.is_staff or obj.is_superuser):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Deactivate instead of deleting; only superusers may delete accounts.
        return request.user.is_superuser and super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if self._is_manager_only(request):
            # Defence in depth: managers can never grant admin rights.
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)


admin.site.unregister(User)
admin.site.register(User, ProtoLearnUserAdmin)
