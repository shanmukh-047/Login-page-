from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_site_path(value):
    if not value.startswith("/") or value.startswith("//") or "\\" in value:
        raise ValidationError("Enter a path on this site that starts with a single '/', e.g. /courses/")


class AccountProfile(models.Model):
    """Per-account settings an admin controls. Holds no credentials."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="protolearn_profile"
    )
    home_path = models.CharField(
        "Home page after login",
        max_length=200,
        blank=True,
        validators=[validate_site_path],
        help_text="Optional. Where this user is sent after logging in, e.g. /courses/. "
        "Leave blank to use the site default.",
    )

    def __str__(self):
        return f"Profile for {self.user}"
