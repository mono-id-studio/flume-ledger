from typing import TypeVar, ClassVar
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models import (
    EmailField,
    CharField,
    BooleanField,
    DateTimeField,
)

UserType = TypeVar("UserType", bound="CustomUser")


class CustomUserManager(UserManager[UserType]):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        extra_fields.pop("username", None)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # type: ignore[assignment]
    email = EmailField(unique=True)
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    is_active = BooleanField(default=True)
    created_at: DateTimeField = DateTimeField(auto_now_add=True)
    updated_at: DateTimeField = DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[CustomUserManager["CustomUser"]] = CustomUserManager()  # type: ignore[assignment]

    def __str__(self):
        return self.email

    def ID(self) -> int:
        return int(str(self.pk))
