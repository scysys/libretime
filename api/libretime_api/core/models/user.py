import hashlib

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Permission
from django.db import models

from ...permission_constants import GROUPS
from .role import Role


class UserManager(BaseUserManager):
    def create_user(self, role, username, password, email, first_name, last_name):
        user = self.model(
            role=role,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, email, first_name, last_name):
        return self.create_user(
            Role.ADMIN,
            username,
            password,
            email,
            first_name,
            last_name,
        )

    def get_by_natural_key(self, username):
        return self.get(username=username)


class User(AbstractBaseUser):
    role = models.CharField(
        db_column="type",
        max_length=1,
        choices=Role.choices,
    )

    username = models.CharField(db_column="login", unique=True, max_length=255)
    password = models.CharField(db_column="pass", max_length=255)
    email = models.CharField(max_length=1024, blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    login_attempts = models.IntegerField(
        db_column="login_attempts",
        blank=True,
        null=True,
    )
    last_login = models.DateTimeField(
        db_column="lastlogin",
        blank=True,
        null=True,
    )
    last_failed_login = models.DateTimeField(
        db_column="lastfail",
        blank=True,
        null=True,
    )

    skype = models.CharField(
        db_column="skype_contact",
        max_length=1024,
        blank=True,
        null=True,
    )
    jabber = models.CharField(
        db_column="jabber_contact",
        max_length=1024,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        db_column="cell_phone",
        max_length=1024,
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "cc_subjs"

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["role", "email", "first_name", "last_name"]
    objects = UserManager()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def set_password(self, raw_password):
        if not raw_password:
            self.set_unusable_password()
        else:
            self.password = hashlib.md5(raw_password.encode()).hexdigest()

    def is_staff(self):
        return self.role == Role.ADMIN

    def check_password(self, raw_password):
        if self.has_usable_password():
            test_password = hashlib.md5(raw_password.encode()).hexdigest()
            return test_password == self.password
        return False

    # The following methods have to be re-implemented here, as PermissionsMixin
    # assumes that the User class has a 'group' attribute, which LibreTime does
    # not currently provide. Once Django starts managing the Database
    # (managed = True), then this can be replaced with
    # django.contrib.auth.models.PermissionMixin.

    def is_superuser(self):
        return self.role == Role.ADMIN

    def get_user_permissions(self, obj=None):
        """
        Users do not have permissions directly, only through groups
        """
        return []

    def get_group_permissions(self, obj=None):
        permissions = GROUPS[self.role]
        if obj:
            obj_name = obj.__class__.__name__.lower()
            permissions = [perm for perm in permissions if obj_name in perm]
        # get permissions objects
        q = models.Q()
        for perm in permissions:
            q = q | models.Q(codename=perm)
        return list(Permission.objects.filter(q))

    def get_all_permissions(self, obj=None):
        return self.get_user_permissions(obj) + self.get_group_permissions(obj)

    def has_perm(self, perm, obj=None):
        if self.is_superuser():
            return True
        if not perm:
            return False
        permissions = self.get_all_permissions(obj)
        try:
            permission = Permission.objects.get(codename=perm)
            return permission in permissions
        except Permission.DoesNotExist:
            return False

    def has_perms(self, perm_list, obj=None):
        result = True
        for permission in perm_list:
            result = result and self.has_perm(permission, obj)
        return result
