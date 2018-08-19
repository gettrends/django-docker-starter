import datetime
import uuid
from django.db import models
from django_extensions.db.fields import ModificationDateTimeField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

from accounts.constants import TOKEN_TYPES


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at', ]


class Role(models.Model):
    def __str__(self):
        return self.name

    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)

    name = models.CharField(max_length=100,
                            help_text="Enter a name for this type of role")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        if self.model.objects.filter(email=email).exists():
            raise ValueError('A user already exists with that email address')

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(email, password, **extra_fields)


class User(PermissionsMixin, AbstractBaseUser):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)

    email = models.EmailField(verbose_name='email address',
                              max_length=255,
                              unique=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(
        auto_now_add=True,
        help_text="Date user joined Reelio"
    )

    last_updated = ModificationDateTimeField(
        help_text="Auto update with timestamp when changes are made"
    )

    role = models.ForeignKey(Role, blank=True, null=True, on_delete=models.PROTECT)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_short_name(self):
        """Returns the short name for the user."""

        return self.email


class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50, choices=TOKEN_TYPES)
    expires = models.DateTimeField()

    def save(self, hours=24, force_insert=False, force_update=False, using=None, update_fields=None):
        self.expires = datetime.datetime.now() + datetime.timedelta(hours=hours)

        super().save()

    def __str__(self):
        return str(self.id)
