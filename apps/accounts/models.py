from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Role(models.TextChoices):
    CUSTOMER = "customer", "Cliente"
    AGENT = "agent", "Agente"
    ADMIN = "admin", "Administrador"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, password, **extra):
        if not email:
            raise ValueError("El email es obligatorio")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        extra.setdefault("role", Role.CUSTOMER)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.ADMIN)
        return self._create(email, password, **extra)


class User(AbstractUser):
    """Usuario propio: login por email y rol. Debe existir antes de la primera migración."""

    username = None
    email = models.EmailField("email", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["first_name", "email"]

    @property
    def full_name(self) -> str:
        return (f"{self.first_name} {self.last_name}").strip() or self.email

    @property
    def is_staff_member(self) -> bool:
        return self.role in (Role.AGENT, Role.ADMIN)

    def __str__(self) -> str:
        return self.email
