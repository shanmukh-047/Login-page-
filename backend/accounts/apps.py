from django.apps import AppConfig
from django.db.models.signals import post_migrate

ACCOUNT_MANAGERS_GROUP = "Account managers"


def ensure_account_managers_group(sender, **kwargs):
    """Create the 'Account managers' group with only the user-management permissions.

    No users or credentials are created here; a superuser assigns staff to this group.
    """
    from django.contrib.auth.models import Group, Permission

    group, _ = Group.objects.get_or_create(name=ACCOUNT_MANAGERS_GROUP)
    codenames = [
        "add_user", "change_user", "view_user",
        "add_accountprofile", "change_accountprofile", "view_accountprofile",
    ]
    perms = Permission.objects.filter(
        content_type__app_label__in=["auth", "accounts"], codename__in=codenames
    )
    group.permissions.add(*perms)


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Accounts"

    def ready(self):
        post_migrate.connect(ensure_account_managers_group, sender=self)
