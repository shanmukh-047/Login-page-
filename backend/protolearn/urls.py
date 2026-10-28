from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ProtoLearn account management"
admin.site.site_title = "ProtoLearn accounts"
admin.site.index_title = "Manage student and customer accounts"

urlpatterns = [
    # /admin is the public React login page, so Django's admin lives at /manage/.
    path("manage/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
]
