import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings

from .apps import ACCOUNT_MANAGERS_GROUP
from .models import AccountProfile

User = get_user_model()
PW = "Str0ng-Initial-Pass!"


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


class LoginApiTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("student1", password=PW)

    def test_correct_credentials_log_in_and_redirect(self):
        r = post_json(self.client, "/api/auth/login/", {"username": "student1", "password": PW})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["redirect"], "/login")
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

    def test_wrong_password_rejected(self):
        r = post_json(self.client, "/api/auth/login/", {"username": "student1", "password": "nope"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["detail"], "Invalid username or password.")

    def test_unknown_user_gets_same_message(self):
        r = post_json(self.client, "/api/auth/login/", {"username": "ghost", "password": PW})
        self.assertEqual(r.json()["detail"], "Invalid username or password.")

    def test_inactive_user_cannot_log_in(self):
        self.student.is_active = False
        self.student.save()
        r = post_json(self.client, "/api/auth/login/", {"username": "student1", "password": PW})
        self.assertEqual(r.status_code, 401)

    def test_empty_fields_rejected(self):
        r = post_json(self.client, "/api/auth/login/", {"username": "", "password": ""})
        self.assertEqual(r.status_code, 400)

    def test_response_never_contains_password_hash(self):
        r = post_json(self.client, "/api/auth/login/", {"username": "student1", "password": PW})
        body = r.content.decode()
        self.assertNotIn("pbkdf2", body)
        self.assertNotIn("password", r.json()["user"])

    def test_password_is_stored_hashed(self):
        self.assertNotEqual(self.student.password, PW)
        self.assertTrue(self.student.password.startswith("pbkdf2_sha256$"))

    def test_per_user_home_page(self):
        AccountProfile.objects.create(user=self.student, home_path="/courses/")
        r = post_json(self.client, "/api/auth/login/", {"username": "student1", "password": PW})
        self.assertEqual(r.json()["redirect"], "/courses/")

    def test_csrf_enforced(self):
        c = Client(enforce_csrf_checks=True)
        r = post_json(c, "/api/auth/login/", {"username": "student1", "password": PW})
        self.assertEqual(r.status_code, 403)
        c.get("/api/auth/csrf/")
        token = c.cookies["csrftoken"].value
        r = c.post("/api/auth/login/", data=json.dumps({"username": "student1", "password": PW}),
                   content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 200)

    def test_no_public_registration_endpoint(self):
        for url in ["/api/auth/register/", "/api/auth/signup/", "/api/auth/users/"]:
            self.assertEqual(post_json(self.client, url, {"username": "x", "password": PW}).status_code, 404)
        self.assertEqual(User.objects.count(), 1)

    def test_logout(self):
        self.client.force_login(self.student)
        self.client.post("/api/auth/logout/")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)


class AdminAccountManagementTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user("manager", password=PW, is_staff=True)
        self.manager.groups.add(Group.objects.get(name=ACCOUNT_MANAGERS_GROUP))
        self.student = User.objects.create_user("student1", password=PW)

    def add_user(self, client, username, pw="N3w-Student-Pass!"):
        return client.post("/manage/auth/user/add/", {
            "username": username, "password1": pw, "password2": pw, "usable_password": "true",
            "protolearn_profile-TOTAL_FORMS": "1", "protolearn_profile-INITIAL_FORMS": "0",
            "protolearn_profile-MIN_NUM_FORMS": "0", "protolearn_profile-MAX_NUM_FORMS": "1",
            "protolearn_profile-0-home_path": "",
        })

    def test_manager_creates_account_and_new_user_can_log_in(self):
        self.client.force_login(self.manager)
        r = self.add_user(self.client, "newstudent")
        self.assertEqual(r.status_code, 302, getattr(r, "context", None) and r.context["adminform"].form.errors)
        u = User.objects.get(username="newstudent")
        self.assertFalse(u.is_staff)
        self.assertTrue(u.password.startswith("pbkdf2_sha256$"))
        c = Client()
        r = post_json(c, "/api/auth/login/", {"username": "newstudent", "password": "N3w-Student-Pass!"})
        self.assertEqual(r.status_code, 200)

    def test_duplicate_username_rejected(self):
        self.client.force_login(self.manager)
        r = self.add_user(self.client, "student1")
        self.assertEqual(r.status_code, 200)  # form re-rendered with an error
        self.assertEqual(User.objects.filter(username="student1").count(), 1)

    def test_manager_can_reset_password(self):
        self.client.force_login(self.manager)
        url = f"/manage/auth/user/{self.student.pk}/password/"
        r = self.client.post(url, {"password1": "Reset-Pass-2026!", "password2": "Reset-Pass-2026!",
                                   "usable_password": "true"})
        self.assertEqual(r.status_code, 302)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("Reset-Pass-2026!"))

    def test_manager_cannot_edit_staff_or_superusers(self):
        boss = User.objects.create_superuser("boss", password=PW)
        self.client.force_login(self.manager)
        r = self.client.get(f"/manage/auth/user/{boss.pk}/change/")
        self.assertNotEqual(r.status_code, 200)
        r = self.client.get(f"/manage/auth/user/{boss.pk}/password/")
        self.assertNotEqual(r.status_code, 200)

    def test_manager_cannot_grant_admin_rights(self):
        self.client.force_login(self.manager)
        r = self.client.get(f"/manage/auth/user/{self.student.pk}/change/")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('name="is_staff"', r.content.decode())
        self.assertNotIn('name="is_superuser"', r.content.decode())

    def test_manager_cannot_delete(self):
        self.client.force_login(self.manager)
        r = self.client.post(f"/manage/auth/user/{self.student.pk}/delete/", {"post": "yes"})
        self.assertEqual(r.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())

    def test_student_cannot_access_admin(self):
        self.client.force_login(self.student)
        r = self.client.get("/manage/auth/user/add/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/manage/login/", r["Location"])

    def test_anonymous_cannot_access_admin(self):
        r = self.client.get("/manage/auth/user/")
        self.assertEqual(r.status_code, 302)

    def test_staff_without_permission_cannot_create(self):
        plain_staff = User.objects.create_user("staff2", password=PW, is_staff=True)
        self.client.force_login(plain_staff)
        self.assertEqual(self.client.get("/manage/auth/user/add/").status_code, 403)

    def test_deactivate_blocks_login(self):
        self.client.force_login(self.manager)
        self.student.is_active = False
        self.student.save()
        r = post_json(Client(), "/api/auth/login/", {"username": "student1", "password": PW})
        self.assertEqual(r.status_code, 401)
