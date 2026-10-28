"""Session-based login API for the React login page.

There is intentionally no registration endpoint: accounts are created by admins in /manage/.
"""
import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

INVALID = "Invalid username or password."


def _public_user(user):
    # Never include password hashes or permission details.
    return {"username": user.get_username(), "first_name": user.first_name, "is_staff": user.is_staff}


def _safe_path(path):
    if path and url_has_allowed_host_and_scheme(path, allowed_hosts=None) and path.startswith("/"):
        return path
    return None


def destination_for(user):
    profile = getattr(user, "protolearn_profile", None)
    if profile is not None and _safe_path(profile.home_path):
        return profile.home_path
    if user.is_staff:
        return _safe_path(settings.PROTOLEARN_STAFF_REDIRECT) or "/"
    return _safe_path(settings.PROTOLEARN_DEFAULT_REDIRECT) or "/"


@require_GET
@ensure_csrf_cookie
@never_cache
def csrf(request):
    """Sets the csrftoken cookie the React page sends back in the X-CSRFToken header."""
    return JsonResponse({"detail": "ok"})


@require_POST
@csrf_protect
@never_cache
def login_view(request):
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": INVALID}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": INVALID}, status=400)

    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")
    if not username or not password:
        return JsonResponse({"detail": "Please enter your username and password."}, status=400)

    # ModelBackend checks the hashed password and refuses inactive accounts.
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"detail": INVALID}, status=401)

    login(request, user)  # rotates the session key
    return JsonResponse({"user": _public_user(user), "redirect": destination_for(user)})


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Logged out."})


@require_GET
@never_cache
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Not logged in."}, status=401)
    return JsonResponse({"user": _public_user(request.user), "redirect": destination_for(request.user)})
